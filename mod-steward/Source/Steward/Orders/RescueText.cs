// Written for RimBridge (2026). Verse-free: the rescue order's summary parts about who is downed.
using System.Collections.Generic;
using System.Linq;

namespace RimBridge.Steward.Orders
{
    public static class RescueText
    {
        public const string NobodyOutside = "nobody downed outside a bed";

        /// <summary>"2 downed in bed (Von, Cave)"; names past the third are counted, not listed. Empty when nobody is.</summary>
        public static string InBed(IReadOnlyList<string> names)
        {
            if (names.Count == 0) return "";
            string shown = string.Join(", ", names.Take(3)) + (names.Count > 3 ? $", +{names.Count - 3} more" : "");
            return $"{names.Count} downed in bed ({shown})";
        }
    }
}
