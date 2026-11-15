using Assets.Scripts.Networking;
using LaunchPadBooster.Networking;

namespace PainterPro
{
    public enum PaintMode : byte
    {
        Network = 1,
        Checkered = 2,
    }

    // Everything needed to paint a network, captured on the machine whose
    // player sprayed. It does not depend on the vanilla AttackWithMessage at
    // all: LaunchPad sends mod messages on its own transport channel, so
    // nothing guarantees the order the two arrive in.
    public struct PaintRequest
    {
        public long PainterId;
        public byte HandSlot;
        public long TargetId;
        public int ColorIndex;
        public PaintMode Mode;
    }

    // Client -> host, sent when a remote player sprays with Shift or Ctrl held.
    public class PaintRequestMessage : INetworkMessage
    {
        public PaintRequest Request;

        public void Serialize(RocketBinaryWriter writer)
        {
            writer.WriteInt64(Request.PainterId);
            writer.WriteByte(Request.HandSlot);
            writer.WriteInt64(Request.TargetId);
            writer.WriteInt32(Request.ColorIndex);
            writer.WriteByte((byte)Request.Mode);
        }

        public void Deserialize(RocketBinaryReader reader)
        {
            Request.PainterId = reader.ReadInt64();
            Request.HandSlot = reader.ReadByte();
            Request.TargetId = reader.ReadInt64();
            Request.ColorIndex = reader.ReadInt32();
            Request.Mode = (PaintMode)reader.ReadByte();
        }

        public void Process(long clientId)
        {
            PainterProPlugin.Log($"request from client {clientId}: {Request.Mode} target={Request.TargetId} colour={Request.ColorIndex}");
            NetworkPaint.Apply(Request);
        }
    }
}
