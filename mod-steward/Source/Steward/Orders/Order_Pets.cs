// Written for RimBridge (2026): the pets standing order.
using System;
using System.Collections.Generic;
using System.Linq;
using Newtonsoft.Json.Linq;
using RimWorld;
using Verse;

namespace RimBridge.Steward.Orders
{
    /// <summary>
    /// Threat onset → record each colony animal's allowed area and restrict it to the allowed area labelled PetSafe.
    /// 600 threat-free ticks → restore the recorded areas. No PetSafe area → nothing moves, the summary and one ledger
    /// event say so. An area changed by hand during the threat is kept and never restored. All state is per map.
    /// </summary>
    public sealed class Order_Pets : Order
    {
        public override string Id => "pets";
        public override string Label => "Pets: shelter colony animals in PetSafe during a threat";
        public override string Doc =>
            "Every 60 ticks the order checks for a threat with the game's own rule (GenHostility.AnyHostileActiveThreatToPlayer); " +
            "a downed hostile counts only while the game still lets it attack. When a threat starts, the order records the allowed " +
            $"area of each colony animal and restricts the animal to the allowed area labelled {PetShelter.SafeArea}. The order never " +
            $"creates or picks this area. If no area is labelled {PetShelter.SafeArea} when a raid comes, the animals stay where they " +
            "are: the summary names the missing area and one pets_no_area ledger event is written for the threat. An animal already " +
            $"restricted to {PetShelter.SafeArea} stays there and is released to unrestricted when the threat clears. Roamers and other animals that cannot take an " +
            $"area restriction are counted, not moved. {PetShelter.ClearAfterTicks} threat-free ticks after the last threat, each animal " +
            "gets its recorded area back (unrestricted if it had none). If the area of a sheltered animal changes during the threat " +
            "(ui.set_policies area, or the game's Animals tab), the order keeps that change and does not restore the animal. An animal " +
            $"with a ui.set_policies:area touch in the last hour is not moved. The order does not check that {PetShelter.SafeArea} is " +
            "roofed or enclosed; the summary and explain give its cell, roofed and indoor counts. Switching the order off while it " +
            "holds animals restores them first.";
        public override int IntervalTicks => 60;
        static readonly string[] Scopes = { "ui.set_policies:area" };
        public override IReadOnlyList<string>? TouchScopes => Scopes;

        public override IEnumerable<string> Explain()
        {
            yield return "threat: GenHostility.AnyHostileActiveThreatToPlayer: a hostile target that is not fogged, awake and not threat-disabled; the game marks a downed pawn threat-disabled unless it can attack while crawling";
            yield return $"area: the allowed area labelled exactly '{PetShelter.SafeArea}' (the first one when several have that label); the order never creates, picks or edits it";
            yield return $"onset: every spawned colony animal that can take an area restriction is restricted to {PetShelter.SafeArea}, its previous area recorded; an animal already in {PetShelter.SafeArea} is recorded as unrestricted, so the clear releases it; animals that arrive later in the threat are restricted on the next pass";
            yield return $"no area: nothing moves; summary 'no allowed area labelled {PetShelter.SafeArea}'; one ledger pets_no_area per threat when an animal was left out";
            yield return $"hands-off: a ui.set_policies:area touch in the last hour, or an area change on a sheltered animal during the threat (any source): the order keeps that area and does not restore the animal";
            yield return $"clear: {PetShelter.ClearAfterTicks} threat-free ticks → each recorded animal still in {PetShelter.SafeArea} gets its recorded area back ('' = unrestricted; a deleted area → unrestricted)";
            yield return $"not checked: whether {PetShelter.SafeArea} is roofed, enclosed or reachable; the cell counts below are reported, not enforced";
            yield return "ledger: pets_sheltered {moved, already, area}, pets_no_area {animals}, pets_released {restored, left, gone}";
            var map = Find.CurrentMap;
            if (map != null)
            {
                var areas = SafeAreas(map);
                yield return areas.Count == 0 ? $"{PetShelter.SafeArea} on this map: none" : $"{PetShelter.SafeArea} on this map: {AreaText(map, areas)}";
            }
            var g = StewardGame.Current;
            if (g != null)
                foreach (var kv in g.PetStates)
                    if (kv.Value.active) yield return $"map {kv.Key}: threat active, {kv.Value.prevArea.Count} held in {PetShelter.SafeArea}, {kv.Value.left.Count} left to you";
        }

        /// <summary>True while the order holds this animal in PetSafe (other steward code leaves its area alone).</summary>
        public static bool Holds(Pawn p)
        {
            var g = StewardGame.Current;
            if (g == null || p?.Map == null) return false;
            var st = g.PetsOrNull(p.Map);
            if (st == null || !st.active || !st.prevArea.ContainsKey(p.ThingID)) return false;
            return StandingOrders.Get<Order_Pets>()?.Enabled ?? false;
        }

        static List<Area> SafeAreas(Map map)
            => map.areaManager.AllAreas.Where(a => a is Area_Allowed && a.Label == PetShelter.SafeArea).ToList();

        /// <summary>"40 cells, 40 roofed, 36 indoors" (plus the duplicate count): what the order reports about the area.</summary>
        static string AreaText(Map map, List<Area> areas)
        {
            var (cells, roofed, indoors) = Counts(map, areas[0]);
            string text = $"{cells} cells, {roofed} roofed, {indoors} indoors";
            if (areas.Count > 1) text += $" ({areas.Count} areas have this label; the first is used)";
            return text;
        }

        static (int cells, int roofed, int indoors) Counts(Map map, Area area)
        {
            int cells = 0, roofed = 0, indoors = 0;
            foreach (var c in area.ActiveCells)
            {
                cells++;
                if (c.Roofed(map)) roofed++;
                var room = c.GetRoom(map);
                if (room != null && !room.PsychologicallyOutdoors) indoors++;
            }
            return (cells, roofed, indoors);
        }

        static JObject AreaJson(Map map, List<Area> areas)
        {
            var (cells, roofed, indoors) = Counts(map, areas[0]);
            return new JObject { ["label"] = PetShelter.SafeArea, ["cells"] = cells, ["roofed"] = roofed, ["indoors"] = indoors, ["labelled"] = areas.Count };
        }

        PetFacts Facts(Pawn p) => new PetFacts
        {
            Id = p.ThingID,
            Area = p.playerSettings?.AreaRestrictionInPawnCurrentMap?.Label ?? "",
            Restrictable = p.playerSettings != null && p.playerSettings.SupportsAllowedAreas,
            AreaTouched = Touched(p),
        };

        // ── run ──

        public override OrderReport Run(Map map)
        {
            var g = StewardGame.Current;
            if (g == null) return OrderReport.Idle("no game state");
            int tick = Find.TickManager.TicksGame;
            var st = g.Pets(map);
            var areas = SafeAreas(map);
            var report = new OrderReport();

            if (GenHostility.AnyHostileActiveThreatToPlayer(map))
            {
                bool onset = PetShelter.Threat(st, tick);
                Shelter(map, st, areas, onset, report);
                return report;
            }
            if (st.active && !PetShelter.ShouldClear(st, tick))
            {
                foreach (var id in st.prevArea.Keys) report.Act(id);
                int left = PetShelter.ClearAfterTicks - (tick - st.lastThreatTick);
                report.Summary = $"no threat; restoring in {Math.Max(0, left)} ticks; {st.prevArea.Count} held in {PetShelter.SafeArea}";
                return report;
            }
            if (st.active)
            {
                Release(map, st, report);
                return report;
            }
            return OrderReport.Idle(areas.Count == 0
                ? $"no threat; no allowed area labelled {PetShelter.SafeArea}"
                : $"no threat; {PetShelter.SafeArea}: {AreaText(map, areas)}");
        }

        void Shelter(Map map, PetState st, List<Area> areas, bool onset, OrderReport report)
        {
            var area = areas.FirstOrDefault();
            int moved = 0, already = 0, held = 0, cannot = 0, handsOff = 0, notMoved = 0;
            var dropped = new List<string>();
            foreach (var p in map.mapPawns.SpawnedColonyAnimals.ToList())
            {
                var f = Facts(p);
                switch (PetShelter.WhileThreat(st, f, area != null))
                {
                    case PetAction.Restrict:
                        p.playerSettings!.AreaRestrictionInPawnCurrentMap = area;
                        moved++;
                        report.Act(p.ThingID);
                        break;
                    case PetAction.Hold:
                        held++;
                        report.Act(p.ThingID);
                        break;
                    case PetAction.Stay:
                        already++;
                        break;
                    case PetAction.Drop:
                        dropped.Add($"{p.LabelShort} (area {(f.Area.Length > 0 ? f.Area : "unrestricted")})");
                        break;
                    default:
                        if (!f.Restrictable) cannot++;
                        else if (f.AreaTouched || st.left.Contains(f.Id)) handsOff++;
                        else { notMoved++; report.Act(p.ThingID); }
                        break;
                }
            }

            if (area == null)
            {
                if (notMoved > 0 && !st.noAreaReported)
                {
                    st.noAreaReported = true;
                    StewardLedger.Orders("pets_no_area", $"{notMoved} colony animal(s) not moved: no allowed area labelled {PetShelter.SafeArea}",
                        new JObject { ["animals"] = notMoved, ["map"] = map.uniqueID });
                }
                report.Summary = $"threat: no allowed area labelled {PetShelter.SafeArea}; {notMoved} animal(s) not moved";
            }
            else
            {
                string areaText = AreaText(map, areas);
                if (moved > 0)
                    StewardLedger.Orders("pets_sheltered", $"{moved} animal(s) restricted to {PetShelter.SafeArea} ({areaText}), {already} already there",
                        new JObject { ["moved"] = moved, ["already"] = already, ["area"] = AreaJson(map, areas), ["map"] = map.uniqueID, ["onset"] = onset });
                report.Summary = $"threat: {st.prevArea.Count} held in {PetShelter.SafeArea}" + (moved > 0 ? $" (+{moved} moved)" : "")
                    + (already > 0 ? $", {already} of them already there" : "") + $"; {PetShelter.SafeArea}: {areaText}";
            }
            if (cannot > 0) report.Summary += $"; {cannot} cannot take an area restriction";
            if (handsOff > 0) report.Summary += $"; {handsOff} hands-off";
            if (dropped.Count > 0) report.Summary += "; area changed by hand, left to you: " + string.Join(", ", dropped);
        }

        // ── release ──

        /// <summary>Restores this map now (used when the order is switched off during a threat); null when nothing is held there.</summary>
        public int? ReleaseNow(Map map)
        {
            var g = StewardGame.Current;
            if (g == null || map == null) return null;
            var st = g.PetsOrNull(map);
            if (st == null || !st.active) return null;
            var report = new OrderReport();
            int restored = Release(map, st, report);
            g.RecordOrderRun(Id, Find.TickManager.TicksGame, report);
            return restored;
        }

        int Release(Map map, PetState st, OrderReport report)
        {
            int restored = 0, gone = 0;
            var left = new List<string>();
            var missing = new List<string>();
            int changedDuring = st.left.Count;
            foreach (var kv in st.prevArea.ToList())
            {
                var p = FindPawn(map, kv.Key);
                var f = p?.playerSettings == null ? null : Facts(p);
                switch (PetShelter.OnClear(st, kv.Key, f))
                {
                    case PetAction.Restore:
                        Area? prev = kv.Value.Length == 0 ? null : map.areaManager.GetLabeled(kv.Value);
                        if (prev == null && kv.Value.Length > 0) missing.Add(kv.Value);
                        p!.playerSettings.AreaRestrictionInPawnCurrentMap = prev;
                        restored++;
                        report.Act(kv.Key);
                        break;
                    case PetAction.Drop:
                        if (p == null) gone++;
                        else left.Add($"{p.LabelShort} (area {(f!.Area.Length > 0 ? f.Area : "unrestricted")}{(f.AreaTouched ? ", ui.set_policies:area" : "")})");
                        break;
                }
            }
            PetShelter.Cleared(st);
            string leftText = left.Count > 0 ? "; left to you: " + string.Join(", ", left) : "";
            string missingText = missing.Count > 0 ? $"; area gone, now unrestricted: {string.Join(", ", missing.Distinct())}" : "";
            string goneText = gone > 0 ? $"; {gone} no longer on the map" : "";
            string changedText = changedDuring > 0 ? $"; {changedDuring} changed by hand during the threat" : "";
            if (restored + left.Count + gone + changedDuring > 0)
                StewardLedger.Orders("pets_released", $"{restored} area(s) restored{leftText}{missingText}{goneText}{changedText}",
                    new JObject { ["restored"] = restored, ["left"] = new JArray(left), ["gone"] = gone, ["changed_during"] = changedDuring, ["missing_areas"] = new JArray(missing.Distinct()), ["map"] = map.uniqueID });
            report.Summary = $"threat over: {restored} area(s) restored{leftText}{missingText}{goneText}{changedText}";
            return restored;
        }

        static Pawn? FindPawn(Map map, string id)
        {
            foreach (var p in map.mapPawns.AllPawnsSpawned) if (p.ThingID == id) return p;
            return null;
        }
    }
}
