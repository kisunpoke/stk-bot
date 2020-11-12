"""If we store any map bgs/banners and player icons, this would handle it."""

import os
import aiohttp        
import aiofiles

async def make_tmp():
    """Check if tmp folder exists, create if it doesn't"""
    #git doesn't make empty folders so
    banner_dir = "./tmp"
    if not os.path.exists(banner_dir):
        print("making tmp dir")
        os.mkdir(banner_dir)
    #print(os.path.abspath("./tmp"))
    #i honestly have no clue where app/tmp/ is but it works so i won't question it

async def make_banner_folder():
    """Check if banner folder exists, create if it doesn't"""
    await make_tmp()
    banner_dir = "./tmp/map-banners"
    if not os.path.exists(banner_dir):
        print("making banner dir")
        os.mkdir(banner_dir)

async def get_banner_fp(set_id):
    banner_fp = f"./tmp/map-banners/{set_id}.jpg"
    if not os.path.exists(banner_fp):
        await make_banner_folder()
        async with aiohttp.ClientSession() as session:
            url = f"https://assets.ppy.sh/beatmaps/{set_id}/covers/cover.jpg"
            async with session.get(url) as resp:
                if resp.status == 200:
                    f = await aiofiles.open(banner_fp, mode='wb')
                    await f.write(await resp.read())
                    await f.close()
                    print(f"saved banner of {set_id}")
    return banner_fp