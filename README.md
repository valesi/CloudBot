# CloudBot

CloudBot is a simple, fast, expandable, and open-source Python IRC Bot!

## Getting CloudBot

There are currently two branches in this repository:
 - **unfinity** *(stable)*: master branch; contains everything in the **gonzobot** branch plus extra customizations like theming and running suppressed regex events.
 - **gonzobot** *(stable)*: mirrors **[/edwardslabs/CloudBot/gonzobot](https://github.com/edwardslabs/CloudBot)**

## Installing CloudBot

Firstly, CloudBot will only run on **Python 3.5 or higher** for asyncio and other modules.

Clone the repository and install requirements on [*nix](https://github.com/CloudBotIRC/CloudBot/wiki/Installing-on-*nix) or [Windows](https://github.com/CloudBotIRC/CloudBot/wiki/Installing-on-Windows), replacing `CloudBotIRC/CloudBot` with `valesi/CloudBot`.

### Running CloudBot

Before you run the bot, copy `config.default.json` to `config.json` and edit it with your preferred settings. You can check if your JSON is valid using [jsonlint.com](http://jsonlint.com/)!

Once you have installed the required dependencies and renamed the config file, you can run the bot! Make sure you are in the root folder of the project:

```
python3 -m cloudbot
```

You can also run the `cloudbot/__main__.py` file directly, which will work from any directory.
```
python3 /path/to/repository/cloudbot/__main__.py
```

## Getting help with CloudBot

### Documentation

The CloudBot documentation is currently somewhat outdated and may not be correct. If you need any help, please visit our [IRC channel](irc://irc.esper.net/cloudbot) and we will be happy to assist you.

To write your own plugins, visit the [Plugins Wiki Page](https://github.com/CloudBotIRC/CloudBot/wiki/Writing-your-first-command-plugin).

More at the [Wiki Main Page](https://github.com/CloudBotIRC/CloudBot/wiki).

### Support

This fork is maintained by Selavi on Freenode and EFnet, and the upstream developers reside in [#CloudBot](irc://irc.esper.net/cloudbot) on [EsperNet](http://esper.net).

If you think you have found a bug/have a idea/suggestion, please **open a issue** here on Github and contact us on IRC!

## Example CloudBots

You can find a number of example bots in [#CloudBot](irc://irc.esper.net/cloudbot "Connect via IRC to #CloudBot on irc.esper.net").

## Changelog

See [CHANGELOG.md](https://github.com/valesi/CloudBot/blob/master/CHANGELOG.md)

## License

CloudBot is **licensed** under the **GPL v3** license. The terms are as follows.

![GPL V3](https://www.gnu.org/graphics/gplv3-127x51.png)
    
    CloudBot

    Copyright © 2011-2015 Luke Rogers / CloudBot Project

    CloudBot is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    CloudBot is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with CloudBot.  If not, see <http://www.gnu.org/licenses/>.
    
This product includes GeoLite2 data created by MaxMind, available from
<a href="http://www.maxmind.com">http://www.maxmind.com</a>. GeoLite2 databases are distributed under the [Creative Commons Attribution-ShareAlike 3.0 Unported License](https://creativecommons.org/licenses/by-sa/3.0/)

![Powered by wordnik](https://www.wordnik.com/img/wordnik_badge_a1.png)

Translations are Powered by [Yandex.Translate](https://translate.yandex.com)

This product uses data from <a href="http://wordnik.com">http://wordnik.com</a> in accordance with the wordnik.com API <a href="http://developer.wordnik.com/#!/terms">terms of service</a>.
