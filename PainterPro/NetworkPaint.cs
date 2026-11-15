using System;
using System.Collections.Generic;
using Assets.Scripts.Objects;
using Assets.Scripts.Objects.Electrical;
using Assets.Scripts.Objects.Items;
using Assets.Scripts.Objects.Pipes;
using Networks;
using Objects.RoboticArm;
using UnityEngine;

namespace PainterPro
{
    // Server side (or singleplayer): paints the network the target belongs to.
    //
    // The target itself is never painted here. Vanilla's own spray paints it
    // and charges the paint for it; painting it here first would make vanilla
    // refuse with "already that colour" whenever this request won the race.
    public static class NetworkPaint
    {
        public static void Apply(PaintRequest request)
        {
            var target = Thing.Find<Thing>(request.TargetId);
            if (target == null)
                return;

            // The request names the player and hand that sprayed; insist they
            // really are holding a sprayer so a request cannot paint on its own.
            var painter = Thing.Find<Thing>(request.PainterId);
            if (!(painter?.Slots[request.HandSlot]?.Get() is ISprayer))
                return;

            bool checkered = request.Mode == PaintMode.Checkered;
            int painted;

            switch (target)
            {
                case Pipe pipe when pipe.PipeNetwork != null:
                    painted = PaintStructures(pipe, pipe.PipeNetwork.StructureList, PipeFilterFor(pipe), request.ColorIndex, checkered);
                    break;
                case Chute chute when chute.ChuteNetwork != null:
                    painted = PaintStructures(chute, chute.ChuteNetwork.StructureList, _ => true, request.ColorIndex, checkered);
                    break;
                case RoboticArmRailBase rail when rail.RoboticArmNetwork != null:
                    painted = PaintStructures(rail, rail.RoboticArmNetwork.StructureList, t => !(t is RoboticArmDock), request.ColorIndex, checkered);
                    break;
                case Cable cable when cable.CableNetwork != null:
                    painted = PaintCables(cable, cable.CableNetwork.CableList, request.ColorIndex, checkered);
                    break;
                default:
                    return;
            }

            PainterProPlugin.Log($"{request.Mode} paint from {target.GetType().Name}: {painted} more painted");
        }

        // A pipe network paints things of the same kind as the one sprayed.
        // Spraying a planter or a vent paints the planters or vents on that
        // network. Spraying a pipe, or any other device on the run, paints
        // only the pipe segments: tanks, connectors and drains carrying half
        // of a checkered gas-mix marking would read as the wrong gas.
        private static Func<Thing, bool> PipeFilterFor(Pipe sprayed)
        {
            if (sprayed is HydroponicTray)
                return t => t is HydroponicTray;
            if (sprayed is PassiveVent)
                return t => t is PassiveVent;
            return t => t is Piping;
        }

        // Checkered colours every second step outward from the sprayed item,
        // counting steps along the network's own connections. A long pipe is
        // one step however many cells it spans, and an unpainted device still
        // counts as a step, so the pattern stays regular across both.
        private static int PaintStructures(INetworkedStructure start, List<INetworkedStructure> members, Func<Thing, bool> include, int colorIndex, bool checkered)
        {
            int count = 0;

            if (!checkered)
            {
                foreach (var member in members)
                    if (member != start && TryPaint(member.GetAsThing, include, colorIndex))
                        count++;
                return count;
            }

            var inNetwork = new HashSet<INetworkedStructure>(members);
            var steps = new Dictionary<INetworkedStructure, int> { [start] = 0 };
            var frontier = new Queue<INetworkedStructure>();
            frontier.Enqueue(start);

            while (frontier.Count > 0)
            {
                var current = frontier.Dequeue();
                int step = steps[current];

                if (step > 0 && step % 2 == 0 && TryPaint(current.GetAsThing, include, colorIndex))
                    count++;

                foreach (var next in current.ConnectedStructures() ?? new List<INetworkedStructure>())
                {
                    if (next == null || !inNetwork.Contains(next) || steps.ContainsKey(next))
                        continue;
                    steps[next] = step + 1;
                    frontier.Enqueue(next);
                }
            }

            return count;
        }

        // Cables expose no neighbour list, but every cable piece fills exactly
        // one small-grid cell, and on a grid of single cells the step count
        // between two pieces always has the same parity as the sum of their
        // cell offsets. So checkered can be decided per cable from its cell.
        private static int PaintCables(Cable start, List<Cable> cables, int colorIndex, bool checkered)
        {
            int count = 0;
            int startParity = CellParity(start);

            foreach (var cable in cables)
            {
                if (cable == start)
                    continue;
                if (checkered && CellParity(cable) != startParity)
                    continue;
                if (TryPaint(cable, _ => true, colorIndex))
                    count++;
            }

            return count;
        }

        // Small-grid cells are 0.5 units apart.
        private static int CellParity(Thing thing)
        {
            var p = thing.Position;
            long sum = Mathf.RoundToInt(p.x * 2f) + Mathf.RoundToInt(p.y * 2f) + Mathf.RoundToInt(p.z * 2f);
            return (int)(sum & 1);
        }

        // Thing.SetCustomColor marks the thing dirty and the game's normal
        // state sync carries the colour to every client.
        private static bool TryPaint(Thing thing, Func<Thing, bool> include, int colorIndex)
        {
            if (thing == null || thing.HasColorState || !include(thing))
                return false;
            thing.SetCustomColor(colorIndex);
            return true;
        }
    }
}
