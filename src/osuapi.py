"""Async functions for interacting with the osu! api.

This uses the v1 endpoint because it is more stable. Use v2 when available or
necessary.
"""
import aiohttp

api_key = open("osukey").read()

async def get_player_data(username):
    #well that's kinda bad
    async with aiohttp.ClientSession() as session:
        player_request = await session.get(f'https://osu.ppy.sh/api/get_user?k={api_key}&u={username}')
        player_data = await player_request.json()
    #print(player_data)
    return player_data[0]

async def get_map_data(diff_id):
    async with aiohttp.ClientSession() as session:
        map_request = await session.get(f'https://osu.ppy.sh/api/get_beatmaps?k={api_key}&b={diff_id}')
        map_data = await map_request.json()
    '''
    thumbnail_url = f'https://b.ppy.sh/thumb/{map_data[0]["beatmapset_id"]}l.jpg'
    map_name = f'{map_data[0]["artist"]} - {map_data[0]["title"]}'
    data = {
        'map_url': map_url,
        'thumbnail_url': thumbnail_url,
        'map_name': map_name
    }
    return data
    '''
    return map_data

async def get_match_data(match_id):
    async with aiohttp.ClientSession() as session:
        match_request = await session.get(f'https://osu.ppy.sh/api/get_match?k={api_key}&mp={match_id}')
        match_data = await match_request.json()
    return match_data
