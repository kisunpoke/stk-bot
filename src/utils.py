"""General commands."""
#maybe help embed stuff?

#unfortunate
#mark is ok below
help = {
    "getmatch":{
        "signature": ("**getmatch** <match_id> [map_index]"),
        "summary":   ("*Get score and statistics data for a match.*"),
        "parameters":(" - *match_id*: /mp link provided by osu!\n"
                      " - *map_index (optional)*: The map index. If not defined, then statistics for the entire match are posted. If defined, then statistics for the nth map are given."),
        "examples":  (" - `getmatch 59424609`: gets general match statistics for the match at https://osu.ppy.sh/mp/59424609\n"
                      " - `getmatch 59424609 2`: gets statistics for the second map played on the same multiplier lobby")
    }
}