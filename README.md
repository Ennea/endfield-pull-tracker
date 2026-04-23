# Endfield Pull Tracker

This tracks your Arknights: Endfield pull history, stores it all in an SQLite database and generates a nice report for an overview.

## Usage

This project is aimed at tech-savvy Linux users. It should also run on Windows, but I haven't tested it.

To grab your pull history, first open the pull history inside the game, then run Endfield Pull Tracker like this:
```sh
LOCALAPPDATA=path/to/AppData/Local ./endfield-pull-tracker.py
```

`LOCALAPPDATA` should point to `AppData/Local` inside the Wine prefix you use for Endfield. Once pulls have been gathered (or updated), you can run the following to generate a report and open it in your default browser:
```sh
./endfield-pull-tracker.py generate-report
```

Pull data is stored in `~/.local/share/endfield-pull-tracker` (or `%APPDATA%\endfield-pull-tracker` on Windows).
