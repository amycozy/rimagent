// Written for RimBridge (2026). Verse-free: the bill fields a production stock job keeps, and the text of a reset.
using System.Collections.Generic;

namespace RimBridge.Steward.Stock
{
    public static class BillKeep
    {
        public const string Mode = "TargetCount";

        /// <summary>Each kept field that differs from the job's value, as "field old → new". Empty when the bill already matches.</summary>
        public static List<string> Changes(string mode, int target, bool suspended, bool pauseWhenSatisfied, int wantTarget)
        {
            var list = new List<string>();
            if (mode != Mode) list.Add($"repeat_mode {mode} → {Mode}");
            if (target != wantTarget) list.Add($"target {target} → {wantTarget}");
            if (suspended) list.Add("suspended true → false");
            if (pauseWhenSatisfied) list.Add("pause_when_satisfied true → false");
            return list;
        }

        public static string ResetNote(string billId, string table, IEnumerable<string> changes)
            => $"reset {billId} on {table}, a bill this job did not add: {string.Join(", ", changes)}";
    }
}
