// Verse-free tests for the pets standing order (shelter on threat, restore on clear, missing area, hands off).
using RimBridge.Steward.Orders;
using Xunit;

namespace RimBridge.Tests
{
    public class PetRulesTests
    {
        const string Safe = PetShelter.SafeArea;

        static PetFacts Pet(string id, string area = "", bool restrictable = true, bool touched = false)
            => new PetFacts { Id = id, Area = area, Restrictable = restrictable, AreaTouched = touched };

        [Fact]
        public void Onset_RecordsTheAreaAndRestricts()
        {
            var st = new PetShelterState();
            Assert.True(PetShelter.Threat(st, 100));
            Assert.False(PetShelter.Threat(st, 160));
            Assert.Equal(PetAction.Restrict, PetShelter.WhileThreat(st, Pet("Cat1"), areaExists: true));
            Assert.Equal(PetAction.Restrict, PetShelter.WhileThreat(st, Pet("Dog2", "Barn"), areaExists: true));
            Assert.Equal("", st.prevArea["Cat1"]);
            Assert.Equal("Barn", st.prevArea["Dog2"]);
            // next pass: both are in PetSafe now and stay held; the record does not change
            Assert.Equal(PetAction.Hold, PetShelter.WhileThreat(st, Pet("Dog2", Safe), areaExists: true));
            Assert.Equal("Barn", st.prevArea["Dog2"]);
        }

        [Fact]
        public void Clear_WaitsThenRestoresEachRecordedArea()
        {
            var st = new PetShelterState();
            PetShelter.Threat(st, 1000);
            PetShelter.WhileThreat(st, Pet("Cat1"), true);
            PetShelter.WhileThreat(st, Pet("Dog2", "Barn"), true);
            Assert.False(PetShelter.ShouldClear(st, 1000 + PetShelter.ClearAfterTicks - 1));
            Assert.True(PetShelter.ShouldClear(st, 1000 + PetShelter.ClearAfterTicks));
            Assert.Equal(PetAction.Restore, PetShelter.OnClear(st, "Cat1", Pet("Cat1", Safe)));
            Assert.Equal(PetAction.Restore, PetShelter.OnClear(st, "Dog2", Pet("Dog2", Safe)));
            Assert.Empty(st.prevArea);
            PetShelter.Cleared(st);
            Assert.False(st.active);
            Assert.False(PetShelter.ShouldClear(st, 99999));
        }

        [Fact]
        public void Clear_DropsAnAnimalThatLeftTheMap()
        {
            var st = new PetShelterState();
            PetShelter.Threat(st, 0);
            PetShelter.WhileThreat(st, Pet("Cat1"), true);
            Assert.Equal(PetAction.Drop, PetShelter.OnClear(st, "Cat1", null));
            Assert.Empty(st.prevArea);
        }

        [Fact]
        public void NoSafeArea_MovesNothing_AndUsesTheAreaOnceItExists()
        {
            var st = new PetShelterState();
            PetShelter.Threat(st, 0);
            Assert.Equal(PetAction.Skip, PetShelter.WhileThreat(st, Pet("Cat1", "Barn"), areaExists: false));
            Assert.Empty(st.prevArea);
            // the director draws PetSafe during the raid: the next pass uses it
            Assert.Equal(PetAction.Restrict, PetShelter.WhileThreat(st, Pet("Cat1", "Barn"), areaExists: true));
            Assert.Equal("Barn", st.prevArea["Cat1"]);
        }

        [Fact]
        public void AlreadyInPetSafe_StaysAndIsReleasedOnClear()
        {
            var st = new PetShelterState();
            PetShelter.Threat(st, 0);
            Assert.Equal(PetAction.Stay, PetShelter.WhileThreat(st, Pet("Cat1", Safe), true));
            Assert.Equal("", st.prevArea["Cat1"]);
            Assert.Equal(PetAction.Hold, PetShelter.WhileThreat(st, Pet("Cat1", Safe), true));
            Assert.Equal(PetAction.Restore, PetShelter.OnClear(st, "Cat1", Pet("Cat1", Safe)));
        }

        [Fact]
        public void HandsOff_AnAreaChangedDuringTheThreatIsKeptAndNotRestored()
        {
            var st = new PetShelterState();
            PetShelter.Threat(st, 0);
            PetShelter.WhileThreat(st, Pet("Cat1", "Barn"), true);
            // the operator moves the cat to another area in the game's Animals tab
            Assert.Equal(PetAction.Drop, PetShelter.WhileThreat(st, Pet("Cat1", "Kitchen"), true));
            Assert.False(st.prevArea.ContainsKey("Cat1"));
            // later passes leave it alone, even when it is back in PetSafe
            Assert.Equal(PetAction.Skip, PetShelter.WhileThreat(st, Pet("Cat1", "Kitchen"), true));
            Assert.Equal(PetAction.Skip, PetShelter.OnClear(st, "Cat1", Pet("Cat1", "Kitchen")));
        }

        [Fact]
        public void HandsOff_ADirectorTouchDropsTheRecordEvenInPetSafe()
        {
            var st = new PetShelterState();
            PetShelter.Threat(st, 0);
            PetShelter.WhileThreat(st, Pet("Cat1", "Barn"), true);
            Assert.Equal(PetAction.Drop, PetShelter.WhileThreat(st, Pet("Cat1", Safe, touched: true), true));
            Assert.Contains("Cat1", st.left);
        }

        [Fact]
        public void HandsOff_AtClearTime_TheChangeWins()
        {
            var st = new PetShelterState();
            PetShelter.Threat(st, 0);
            PetShelter.WhileThreat(st, Pet("Cat1", "Barn"), true);
            Assert.Equal(PetAction.Drop, PetShelter.OnClear(st, "Cat1", Pet("Cat1", "Kitchen")));
            PetShelter.WhileThreat(st, Pet("Dog2", "Barn"), true);
            Assert.Equal(PetAction.Drop, PetShelter.OnClear(st, "Dog2", Pet("Dog2", Safe, touched: true)));
        }

        [Fact]
        public void Skips_TouchedAndUnrestrictableAnimals()
        {
            var st = new PetShelterState();
            PetShelter.Threat(st, 0);
            Assert.Equal(PetAction.Skip, PetShelter.WhileThreat(st, Pet("Cow1", restrictable: false), true));
            Assert.Equal(PetAction.Skip, PetShelter.WhileThreat(st, Pet("Cat1", touched: true), true));
            Assert.Empty(st.prevArea);
        }

        [Fact]
        public void ANewThreat_ForgetsTheLastThreatsHandsOffList()
        {
            var st = new PetShelterState();
            PetShelter.Threat(st, 0);
            PetShelter.WhileThreat(st, Pet("Cat1", "Barn"), true);
            PetShelter.WhileThreat(st, Pet("Cat1", "Kitchen"), true);
            PetShelter.Cleared(st);
            Assert.True(PetShelter.Threat(st, 5000));
            Assert.Equal(PetAction.Restrict, PetShelter.WhileThreat(st, Pet("Cat1", "Kitchen"), true));
        }
    }
}
