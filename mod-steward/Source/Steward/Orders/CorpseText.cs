// Written for RimBridge (2026). Verse-free: the corpses order's text for human corpses it leaves.
using System.Collections.Generic;
using System.Linq;

namespace RimBridge.Steward.Orders
{
    public static class CorpseText
    {
        /// <summary>"1 human corpse left (Dennis): no grave, corpse stockpile or crematorium"; empty when none is left.</summary>
        public static string HumansLeft(IReadOnlyList<string> names)
        {
            if (names.Count == 0) return "";
            string shown = string.Join(", ", names.Take(3)) + (names.Count > 3 ? $", +{names.Count - 3} more" : "");
            string noun = names.Count == 1 ? "human corpse" : "human corpses";
            return $"{names.Count} {noun} left ({shown}): no grave, corpse stockpile or crematorium";
        }
    }
}
