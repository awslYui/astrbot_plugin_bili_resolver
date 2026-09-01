import sys
import types
import unittest
from pathlib import Path


class _Logger:
    def __getattr__(self, _name):
        return lambda *_args, **_kwargs: None


astrbot = types.ModuleType("astrbot")
astrbot_api = types.ModuleType("astrbot.api")
astrbot_api.logger = _Logger()
astrbot.api = astrbot_api
sys.modules.setdefault("astrbot", astrbot)
sys.modules.setdefault("astrbot.api", astrbot_api)

repo_parent = str(Path(__file__).resolve().parents[2])
if repo_parent not in sys.path:
    sys.path.insert(0, repo_parent)

from bilijiexi import analysis_bilibili  # noqa: E402
from bilijiexi.errors import BiliRiskControlError  # noqa: E402


class _Response:
    def __init__(self, status=200, payload=None, url="https://api.bilibili.com/test"):
        self.status_code = status
        self._payload = payload or {}
        self.url = url
        self.headers = {}

    def json(self):
        return self._payload


class _Session:
    def __init__(self, response):
        self.response = response

    async def get(self, *_args, **_kwargs):
        return self.response


class AnalysisTests(unittest.IsolatedAsyncioTestCase):
    async def test_video_extract_uses_anonymous_wbi_endpoint(self):
        url, _page, _time_location = analysis_bilibili.extract(
            "BV1gNtP6aEM4"
        )
        self.assertEqual(
            url,
            "https://api.bilibili.com/x/web-interface/wbi/view"
            "?bvid=BV1gNtP6aEM4",
        )

    async def test_video_description_is_not_truncated(self):
        description = "第一行\n第二行\n第三行\n第四行\n第五行"
        payload = {
            "data": {
                "aid": 123,
                "bvid": "BV1234567890",
                "title": "测试视频",
                "desc": description,
                "pubdate": 0,
                "duration": 60,
                "copyright": 1,
                "tname": "测试",
                "pic": "https://i0.hdslb.com/test.jpg",
                "pages": [{"part": "测试视频"}],
                "owner": {"name": "UP", "mid": 1},
                "stat": {
                    "like": 1,
                    "coin": 2,
                    "favorite": 3,
                    "share": 4,
                    "view": 5,
                    "danmaku": 6,
                    "reply": 7,
                },
            }
        }
        old_display = analysis_bilibili.analysis_display_image
        old_template = analysis_bilibili.analysis_video_template
        try:
            analysis_bilibili.analysis_display_image = False
            analysis_bilibili.analysis_video_template = ""
            message, _ = await analysis_bilibili.video_detail(
                "https://api.bilibili.com/x/web-interface/wbi/view?aid=123",
                session=_Session(_Response(payload=payload)),
            )
        finally:
            analysis_bilibili.analysis_display_image = old_display
            analysis_bilibili.analysis_video_template = old_template

        self.assertIn(description, "".join(message))
        self.assertNotIn("……", "".join(message))

    async def test_video_http_412_is_propagated(self):
        with self.assertRaises(BiliRiskControlError):
            await analysis_bilibili.video_detail(
                "https://api.bilibili.com/x/web-interface/wbi/view?aid=123",
                session=_Session(_Response(status=412)),
            )

    async def test_video_json_minus_412_is_propagated(self):
        with self.assertRaises(BiliRiskControlError):
            await analysis_bilibili.video_detail(
                "https://api.bilibili.com/x/web-interface/wbi/view?aid=123",
                session=_Session(
                    _Response(payload={"code": -412, "message": "请求被拦截"})
                ),
            )

    async def test_short_link_http_412_is_propagated(self):
        with self.assertRaises(BiliRiskControlError):
            await analysis_bilibili.b23_extract(
                "https://b23.tv/abcdef",
                session=_Session(_Response(status=412)),
            )


if __name__ == "__main__":
    unittest.main()
