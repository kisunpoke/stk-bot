"""If we store any map bgs/banners and player icons, this would handle it."""

import os
import aiohttp        
import aiofiles

async def make_banner_folder():
    """Check if banner folder exists, create if it doesn't"""
    #git doesn't make empty folders so
    banner_dir = "./tmp/map-banners"
    print("making banner dir")
    if not os.path.exists(banner_dir):
        os.mkdir(banner_dir)

async def get_banner(set_id):
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
    else:
        pass