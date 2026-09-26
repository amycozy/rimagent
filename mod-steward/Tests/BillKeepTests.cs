// Verse-free tests for the bill fields a production stock job keeps.
using RimBridge.Steward.Stock;
using Xunit;

namespace RimBridge.Tests
{
    public class BillKeepTests
    {
        [Fact]
        public void Changes_EmptyWhenTheBillMatches()
        {
            Assert.Empty(BillKeep.Changes("TargetCount", 22, false, false, 22));
        }

        [Fact]
        public void Changes_NamesEachFieldWithOldAndNewValue()
        {
            var c = BillKeep.Changes("Forever", 10, true, true, 22);
            Assert.Equal(new[]
            {
                "repeat_mode Forever → TargetCount",
                "target 10 → 22",
                "suspended true → false",
                "pause_when_satisfied true → false",
            }, c);
        }

        [Fact]
        public void ResetNote_NamesTheBillAndTheTable()
        {
            var note = BillKeep.ResetNote("Bill_CookMealSimple_2", "Campfire14732", BillKeep.Changes("Forever", 10, false, false, 10));
            Assert.Equal("reset Bill_CookMealSimple_2 on Campfire14732, a bill this job did not add: repeat_mode Forever → TargetCount", note);
        }
    }
}
