"""Drive the real launcher corresponding to the image under test."""


def replay_for_host(source, metadata):
    if metadata.get("host") == "list-menu":
        # Seed only the stock cursor store. Enter the added row using real keys.
        return source.replace("...PLAYER_PARSER,", "...PLAYER_PARSER, tab:'7,2,1',")
    return source


def flappy_entry(metadata):
    if metadata.get("host") == "list-menu":
        return "s1 menu down down down ok ok up up ok "
    return "s1 ok ok " + "down " * 13 + "ok " + "down " * 4 + "ok "
