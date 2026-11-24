def stop(completed, markers):
    if completed:
        return "already finished"
    markers.add("stop-requested")
    return "requested"
