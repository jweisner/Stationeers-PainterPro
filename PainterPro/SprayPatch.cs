using System;
using Assets.Scripts;
using Assets.Scripts.Objects;
using Assets.Scripts.Objects.Items;
using HarmonyLib;
using LaunchPadBooster.Networking;
using UnityEngine;

namespace PainterPro
{
    // OnServer.AttackWith runs only on the machine whose player used the
    // tool: it does the attack locally when that machine simulates (singleplayer
    // or listen-server host) and forwards it as an AttackWithMessage when it is
    // a remote client. The server applies a forwarded attack without calling
    // this method, so the postfix fires exactly once per spray, where the
    // player's keys can actually be read.
    [HarmonyPatch(typeof(OnServer), nameof(OnServer.AttackWith))]
    public static class SprayPatch
    {
        public static void Postfix(Thing attackParent, byte activeHandSlotId, long targetId)
        {
            try
            {
                if (!TryBuildRequest(attackParent, activeHandSlotId, targetId, out var request))
                    return;

                if (GameManager.RunSimulation)
                    NetworkPaint.Apply(request);
                else
                    new PaintRequestMessage { Request = request }.SendToHost();
            }
            catch (Exception e)
            {
                Debug.LogException(e);
            }
        }

        private static bool TryBuildRequest(Thing painter, byte handSlot, long targetId, out PaintRequest request)
        {
            request = default;

            PaintMode mode;
            if (KeyManager.GetButton(KeyCode.LeftShift))
                mode = PaintMode.Network;
            else if (KeyManager.GetButton(KeyCode.LeftControl))
                mode = PaintMode.Checkered;
            else
                return false;

            if (!(painter?.Slots[handSlot]?.Get() is ISprayer sprayer))
                return false;

            // Same preconditions vanilla checks before it will spray at all.
            var material = sprayer.GetPaintMaterial();
            if (material == null || sprayer.IsEmpty)
                return false;
            if (sprayer is Tool tool && !tool.OnOff)
                return false;

            request = new PaintRequest
            {
                PainterId = painter.ReferenceId,
                HandSlot = handSlot,
                TargetId = targetId,
                ColorIndex = GameManager.GetColorSwatch(material).Index,
                Mode = mode,
            };
            return true;
        }
    }
}
