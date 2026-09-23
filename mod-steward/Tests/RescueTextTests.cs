// Verse-free tests for the rescue order's text about who is downed.
using RimBridge.Steward.Orders;
using Xunit;

namespace RimBridge.Tests
{
    public class RescueTextTests
    {
        [Fact]
        public void InBed_EmptyWhenNobody()
        {
            Assert.Equal("", RescueText.InBed(new string[0]));
        }

        [Fact]
        public void InBed_NamesEachPawnUpToThree()
        {
            Assert.Equal("1 downed in bed (Von)", RescueText.InBed(new[] { "Von" }));
            Assert.Equal("4 downed in bed (A, B, C, +1 more)", RescueText.InBed(new[] { "A", "B", "C", "D" }));
        }
    }
}
