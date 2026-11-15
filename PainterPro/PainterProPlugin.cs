using System;
using BepInEx;
using HarmonyLib;
using LaunchPadBooster;
using UnityEngine;

namespace PainterPro
{
    [BepInPlugin(Guid, Name, Version)]
    public class PainterProPlugin : BaseUnityPlugin
    {
        public const string Guid = "net.pbmagnet.stationeers.PainterPro";
        public const string Name = "PainterPro";
        public const string Version = "1.1";

        public static readonly Mod MOD = new Mod(Name, Version);

        void Awake()
        {
            MOD.Networking.RegisterMessage<PaintRequestMessage>();

            // One patch class, patched on its own so a game update that
            // breaks it is logged rather than taking the plugin down.
            try
            {
                new Harmony(Guid).CreateClassProcessor(typeof(SprayPatch)).Patch();
                Log("ready");
            }
            catch (Exception e)
            {
                Debug.LogError($"[{Name}] failed to patch OnServer.AttackWith, painting is vanilla only: {e}");
            }
        }

        internal static void Log(string message) => Debug.Log($"[{Name}] {message}");
    }
}
