#!/usr/bin/perl

use strict;
use warnings;
use List::Util qw(sum);

use constant {
    PATH_TO_SMC         => "/Applications/smcFanControl.app/Contents/Resources/smc",
    MIN_FAN_SPEED_RPM   => 1000,
    LOW_TEMP_THRESHOLD  => 50.0,
    HIGH_TEMP_THRESHOLD => 65.0,
    FREQUENCY_PER_MIN   => 30
};

my $has_default_settings = 1;
my $no_cores = `sysctl -n hw.physicalcpu`;
my @history = ();

sub get_cpu_core_temp
{
    my $cpu_core_temp_info = `@{[PATH_TO_SMC]} -r -k TC@{[@_]}c`;
    return $1 if ($cpu_core_temp_info =~ /.+\]\s+(.+)\s\(/g);
}

sub get_cpu_temp
{
    return sum(map { get_cpu_core_temp($_) } (0..$no_cores - 1)) / $no_cores;
}

sub run_smc_write_cmd
{
    my ($key, $value) = @_;
    my @args = (PATH_TO_SMC, "-k", $key, "-w", $value);
    system(@args);
}

sub set_fan_speed
{
    my ($speed) = @_;
    run_smc_write_cmd("F0Md", "01");
    run_smc_write_cmd("F0Tg", unpack("H*", pack("f", $speed)));
}

sub set_default_fan_settings
{
    run_smc_write_cmd("F0Md", "00");
}

sub meets_default_settings_requirements
{
    my ($cpu_temp, $avg_cpu_temp_last_min) = @_;

    # Apply default settings if:
    #   * there is a spike in the current CPU temperature;
    #   * or if the average CPU temperature over the last minute is greater than LOW_TEMP_THRESHOLD.
    return ($cpu_temp >= HIGH_TEMP_THRESHOLD) || ($avg_cpu_temp_last_min >= LOW_TEMP_THRESHOLD);
}

sub adjust_fan_settings
{
    # Get the current CPU temperature.
    my $cpu_temp = get_cpu_temp();

    # Calculate the average CPU temperature over the last minute.
    push(@history, $cpu_temp);
    shift(@history) if (scalar(@history) > FREQUENCY_PER_MIN);
    my $avg_cpu_temp_last_min = sum(@history) / scalar(@history);

    if (meets_default_settings_requirements($cpu_temp, $avg_cpu_temp_last_min))
    {
        if (not($has_default_settings))
        {
            set_default_fan_settings();
            $has_default_settings = 1;
        }
    }
    else
    {
        if ($has_default_settings)
        {
            set_fan_speed(MIN_FAN_SPEED_RPM);
            $has_default_settings = 0;
        }
    }
}

sub run()
{
    my $start_time = time;
    my $no_seconds = 60.0 / FREQUENCY_PER_MIN;

    while (1)
    {
        adjust_fan_settings();
        sleep($no_seconds - ((time - $start_time) % $no_seconds));
    }
}

run();
