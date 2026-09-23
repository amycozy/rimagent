// Verse-free tests for the corpses order's text about human corpses it leaves.
using RimBridge.Steward.Orders;
using Xunit;

namespace RimBridge.Tests
{
    public class CorpseTextTests
    {
        [Fact]
        public void HumansLeft_EmptyWhenNoneLeft()
        {
            Assert.Equal("", CorpseText.HumansLeft(new string[0]));
        }

        [Fact]
        public void HumansLeft_NamesTheCorpsesAndTheMissingTargets()
        {
            Assert.Equal("1 human corpse left (Dennis): no grave, corpse stockpile or crematorium", CorpseText.HumansLeft(new[] { "Dennis" }));
            Assert.Equal("4 human corpses left (A, B, C, +1 more): no grave, corpse stockpile or crematorium", CorpseText.HumansLeft(new[] { "A", "B", "C", "D" }));
        }
    }
}
