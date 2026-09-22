// Written for RimBridge (2026). Verse-free rules behind the pets standing order (shelter on threat, restore on clear,
// hands off after a change by hand); shared with the unit tests in mod-steward/Tests.
using System.Collections.Generic;

namespace RimBridge.Steward.Orders
{
    /// <summary>Facts about one colony animal, filled by the pets order from the live pawn.</summary>
    public sealed class PetFacts
    {
        public string Id = "";
        /// <summary>Label of its allowed area on this map; "" = unrestricted.</summary>
        public string Area = "";
        /// <summary>Pawn_PlayerSettings.SupportsAllowedAreas: false for roamers and races without area control.</summary>
        public bool Restrictable = true;
        /// <summary>A live ui.set_policies:area touch.</summary>
        public bool AreaTouched;
    }

    public enum PetAction
    {
        /// <summary>Nothing to do (not restrictable, touched, taken over by hand, or no PetSafe area).</summary>
        Skip,
        /// <summary>Already restricted to PetSafe before the order acted: it stays, and is released to unrestricted on clear.</summary>
        Stay,
        /// <summary>Record the current area, restrict to PetSafe.</summary>
        Restrict,
        /// <summary>Recorded and still in PetSafe: keep it there.</summary>
        Hold,
        /// <summary>Its area changed by hand: forget the record, never restore.</summary>
        Drop,
        /// <summary>Threat over: put the recorded area back.</summary>
        Restore,
    }

    /// <summary>The pets order's state on one map. Persisted by PetState.</summary>
    public class PetShelterState
    {
        public bool active;
        public int lastThreatTick = -1;
        /// <summary>pawn id → area label before the order restricted it ("" = unrestricted).</summary>
        public Dictionary<string, string> prevArea = new Dictionary<string, string>();
        /// <summary>Animals whose area changed by hand during this threat: left alone until the threat clears.</summary>
        public HashSet<string> left = new HashSet<string>();
        public bool noAreaReported;
    }

    public static class PetShelter
    {
        public const string SafeArea = "PetSafe";
        public const int ClearAfterTicks = 600;

        /// <summary>Threat seen at `now`; true on onset (the first pass of a threat).</summary>
        public static bool Threat(PetShelterState st, int now)
        {
            st.lastThreatTick = now;
            if (st.active) return false;
            st.active = true;
            st.noAreaReported = false;
            st.left.Clear();
            return true;
        }

        public static bool ShouldClear(PetShelterState st, int now)
            => st.active && (st.lastThreatTick < 0 || now - st.lastThreatTick >= ClearAfterTicks);

        /// <summary>One animal during a threat. Records what it restricts and forgets what was changed by hand.</summary>
        public static PetAction WhileThreat(PetShelterState st, PetFacts f, bool areaExists)
        {
            if (st.prevArea.ContainsKey(f.Id))
            {
                if (f.Area == SafeArea && !f.AreaTouched) return PetAction.Hold;
                st.prevArea.Remove(f.Id);
                st.left.Add(f.Id);
                return PetAction.Drop;
            }
            if (st.left.Contains(f.Id) || !f.Restrictable || f.AreaTouched) return PetAction.Skip;
            // Released on clear, not left in PetSafe: an animal confined there starves, or eats the colony's food.
            if (f.Area == SafeArea) { st.prevArea[f.Id] = ""; return PetAction.Stay; }
            if (!areaExists) return PetAction.Skip;
            st.prevArea[f.Id] = f.Area ?? "";
            return PetAction.Restrict;
        }

        /// <summary>One recorded animal after the threat (null = no longer on the map). Removes the record.</summary>
        public static PetAction OnClear(PetShelterState st, string id, PetFacts? f)
        {
            if (!st.prevArea.ContainsKey(id)) return PetAction.Skip;
            st.prevArea.Remove(id);
            if (f == null || f.Area != SafeArea || f.AreaTouched) return PetAction.Drop;
            return PetAction.Restore;
        }

        /// <summary>Ends the threat once every record is handled.</summary>
        public static void Cleared(PetShelterState st)
        {
            st.active = false;
            st.lastThreatTick = -1;
            st.noAreaReported = false;
            st.left.Clear();
        }
    }
}
