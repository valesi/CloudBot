import os
import platform
import time
from datetime import timedelta

try:
    import psutil
except ImportError:
    psutil = None

from cloudbot import hook
from cloudbot.util.filesize import size as format_bytes
import cloudbot


def _get_repo_link(bot):
    return bot.config.get(
        'repo_link', 'https://github.com/valesi/CloudBot/'
    )


@hook.command("about", "version", "source", autohelp=False)
def about(bot):
    """- Gives name, version, license, and source code of CloudBot."""
    return "CloudBot v{} (unfinity) [div] {} [div] GPLv3".format(cloudbot.__version__, _get_repo_link(bot))


@hook.command(autohelp=False)
def system(reply, message):
    """- Retrieves information about the host system."""

    # Get general system info
    sys_os = platform.platform()
    python_implementation = platform.python_implementation()
    python_version = platform.python_version()
    sys_architecture = '-'.join(platform.architecture())
    sys_cpu_count = platform.machine()

    reply(
        "[h1]OS:[/h1] {} [div] "
        "[h1]Python:[/h1] {} {} [div] "
        "[h1]Architecture:[/h1] {} ({})"
        .format(
            sys_os,
            python_implementation,
            python_version,
            sys_architecture,
            sys_cpu_count)
    )

    if psutil:
        process = psutil.Process(os.getpid())

        # get the data we need using the Process we got
        cpu_usage = process.cpu_percent(1)
        thread_count = process.num_threads()
        memory_usage = format_bytes(process.memory_info()[0])
        uptime = timedelta(seconds=round(time.time() - process.create_time()))

        message(
            "[h1]Uptime:[/h1] {} [div] "
            "[h1]Threads:[/h1] {} [div] "
            "[h1]CPU Usage:[/h1] {} [div] "
            "[h1]Memory Usage:[/h1] {}"
            .format(
                uptime,
                thread_count,
                cpu_usage,
                memory_usage)
        )
