# PainterPro

A Stationeers mod that paints a whole pipe, cable, chute or robotic arm rail
network in one go.

## Controls

With the spray gun in hand:

| Input | Effect |
|---|---|
| Paint | Paints only the item you spray (vanilla behaviour) |
| Shift + paint | Paints the entire connected network |
| Ctrl + paint | Paints a checkered pattern across the network |

Pipe networks paint only the pipe segments themselves. Devices on the run
(in-line tanks, vents, drains, connectors, planters) are left alone, so a
checkered gas-mix marking never lands half on a tank.

Works in singleplayer, on a listen server and on a dedicated server. The mod
must be installed on the server and on every client.

## Install

Requires [StationeersLaunchPad](https://github.com/StationeersLaunchPad/StationeersLaunchPad).

Unzip the release into your Stationeers `mods/` directory so you end up with
`mods/PainterPro/PainterPro.dll` and `mods/PainterPro/About/`.

If you have NetworkPainter installed, remove it first. Both mods patch the
same game method, and running them together paints everything twice.

## Building

Set your game path in `Stationeers.User.props`, then:

```
dotnet build PainterPro
```

To copy the build straight into your local mods directory, create a
`Deploy.User.props` beside it that sets `StationeersSaveDataDirectory`.

## Credits

Inspired by [NetworkPainter](https://github.com/Elmotrix/NetworkPainter) by
Elmotrix. PainterPro began as a fork of it and has since been rewritten from
scratch, with its own multiplayer design.

## License

Apache License 2.0. See [LICENSE](LICENSE).
