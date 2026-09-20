import aiohttp
from xyrondownloader import logger

_INNERTUBE_URL = "https://www.youtube.com/youtubei/v1/search"
_INNERTUBE_KEY = "AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"
_INNERTUBE_HEADERS = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}
_INNERTUBE_CONTEXT = {
    "client": {
        "clientName": "WEB",
        "clientVersion": "2.20240801.00.00",
        "hl": "en",
        "gl": "US",
    }
}


async def youtube_search(query, max_results=50):
    payload = {
        "context": {"client": _INNERTUBE_CONTEXT["client"]},
        "query": query,
    }

    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                f"{_INNERTUBE_URL}?key={_INNERTUBE_KEY}",
                json=payload,
                headers=_INNERTUBE_HEADERS,
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"InnerTube returned {resp.status}")
                    return []
                data = await resp.json()

        results = []
        seen_ids = set()

        sections = (
            data.get("contents", {})
            .get("twoColumnSearchResultsRenderer", {})
            .get("primaryContents", {})
            .get("sectionListRenderer", {})
            .get("contents", [])
        )

        for section in sections:
            items = section.get("itemSectionRenderer", {}).get("contents", [])
            for item in items:
                video = item.get("videoRenderer")
                if not video:
                    continue

                vid_id = video.get("videoId", "")
                if not vid_id or vid_id in seen_ids:
                    continue
                seen_ids.add(vid_id)

                title_runs = video.get("title", {}).get("runs", [])
                title = title_runs[0].get("text", "Unknown") if title_runs else "Unknown"

                owner_runs = video.get("ownerText", {}).get("runs", [])
                channel = owner_runs[0].get("text", "Unknown") if owner_runs else "Unknown"

                duration = video.get("lengthText", {}).get("simpleText", "Live")

                thumbs = video.get("thumbnail", {}).get("thumbnails", [])
                thumb = thumbs[-1].get("url") if thumbs else None

                results.append({
                    "id": vid_id,
                    "title": title,
                    "channel": channel,
                    "duration": duration,
                    "thumb": thumb,
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                })

                if len(results) >= max_results:
                    break
            if len(results) >= max_results:
                break

        return results

    except Exception as e:
        logger.error(f"InnerTube search failed: {e}")
        return []
