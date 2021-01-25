# 2020-iMac-fan-control

A tool that automatically reduces the fan speed of 2020 iMacs to 1000rpm if certain conditions are met. `Python 3.8` and `Perl 5.28` implementations are provided, along with instructions on how to launch the tool automatically after each login. Do **NOT** run this tool on any other Macs (including pre-2020 iMacs)!

## Implementation

Every two seconds the tool grabs the current CPU temperature (as an average across all cores) and computes the average CPU temperature over the last minute. To account for both a spike in CPU activity and a rather constant but moderate use of CPU, two thresholds have been set up:
1. `HIGH_TEMP_THRESHOLD` (65 degrees Celsius);
2. `LOW_TEMP_THRESHOLD` (50 degrees Celsius).

For example, if the CPU is idling and its temperature is around 40ºC across all CPU cores, then "silent mode" (1000rpm) can be safely enabled. However, if there is a quick burst in CPU activity and the temps jump up to 70-80ºC instantly, then it makes sense to leave the "silent mode" and simply restore the default fan settings. To be on the safe side, the average computed over the last minute ensures that the 1000rpm setting is only applied when the temperatures have settled below 50ºC.

## Running the tool in the background

The following guide applies to the Perl implementation (but it can easily be adapted for the Python version as well):

1. Download [smcFanControl](https://github.com/hholtmann/smcFanControl) version 2.6 from [this link](https://github.com/hholtmann/smcFanControl/releases/tag/2.6) and install `smcFanControl.app` under the `/Applications` folder. Do **NOT** open this application at any time!

2. Create a new file called `imac_fan_control.pl` in a suitable directory with the contents of `main.pl`. Mark this file as executable, e.g. `chmod +x <path_to_file>`.

3. Create `iMac.fan.control.plist` inside `~/Library/LaunchAgents` (the tilde matters!) with the following contents:

        <?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
        <plist version="1.0">
        <dict>
            <key>Label</key>
            <string>iMac.fan.control</string>
            <key>RunAtLoad</key>
            <true/>
            <key>Program</key>
            <string>PATH_TO_PERL_SCRIPT</string>
        </dict>
        </plist>

    The placeholder `PATH_TO_PERL_SCRIPT` must be replaced with the **full path** to `imac_fan_control.pl`, e.g. `/Users/username/folder1/folder2/imac_fan_control.pl`. Do **NOT** use the tilde to denote the home directory!

4. Inside the shell, run the following command to begin the automatic switching between "silent mode" and factory settings (again, do **NOT** open `smcFanControl.app`):

        launchctl load -w ~/Library/LaunchAgents/iMac.fan.control.plist

    Note that the `RunAtLoad` key is set to `true` in the above `.plist` file, which means that the job will always start in the background after each login. Thus, the previous command should be run only once.

## Restoring factory settings

The default fan behaviour can be re-enabled via the following commands:
```
launchctl unload -w ~/Library/LaunchAgents/iMac.fan.control.plist
/Applications/smcFanControl.app/Contents/Resources/smc -k F0Md -w 00
```

## Troubleshooting
The `launchctl load` command may fail to run the tool in the background. This can be determined by creating a file called `stderr.log` and adding the following at the end of the `.plist` file (the placeholder `PATH_TO_STDERR_LOG` represents the full path to the log file):
```
<key>StandardErrorPath</key>
<string>PATH_TO_STDERR_LOG</string>
```

If the message
```
Can't open perl script <path_to_perl_script>: Operation not permitted
```
appears in this log file, then it means that the `perl` executable (usually located at `/usr/bin/perl`) doesn't have **Full Disk Access** under macOS.

To fix this, open **System Preferences** and navigate to the **Privacy** tab under **Security & Privacy**. Scroll down to **Full Disk Access** on the left-hand side, unlock the padlock if needed, and then click on the **+** button to add a new item. Now press `CMD + SHIFT + .` to expose all files and folders on the filesystem, and add `/usr/bin/perl` (or the relevant path) to the list of items with Full Disk Access.

Note that the same privileges might be needed for the UNIX shell (e.g. `Terminal.app`).
