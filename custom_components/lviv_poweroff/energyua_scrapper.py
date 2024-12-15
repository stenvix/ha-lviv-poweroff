"""Provides classes for scraping power off periods from the Energy UA website."""

import re

import aiohttp
from bs4 import BeautifulSoup

from .const import PowerOffGroup
from .entities import PowerOffPeriod

URL = "https://lviv.energy-ua.info/grupa/{}"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
TIMEPATTERN = r'^\d{2}:\d{2}$'

class EnergyUaScrapper:
    """Class for scraping power off periods from the Energy UA website."""

    def __init__(self, group: PowerOffGroup) -> None:
        """Initialize the EnergyUaScrapper object."""
        self.group = group

    async def validate(self) -> bool:
        async with (
            aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session,
            session.get(URL.format(self.group)) as response,
        ):
            return response.status == 200

    # @staticmethod
    # def merge_periods(periods: list[PowerOffPeriod]) -> list[PowerOffPeriod]:
    #     if not periods:
    #         return []

    #     periods.sort(key=lambda x: x.startHour)

    #     merged_periods = [periods[0]]
    #     for current in periods[1:]:
    #         last = merged_periods[-1]
    #         if current.startHour <= last.endHour:  # Overlapping or contiguous periods
    #             last.end = max(last.end, current.end)
    #             continue
    #         merged_periods.append(current)

    #     return merged_periods

    async def get_power_off_periods(self) -> list[PowerOffPeriod]:
        async with (
            aiohttp.ClientSession(headers={"User-Agent": USER_AGENT}) as session,
            session.get(URL.format(self.group)) as response,
        ):
            content = await response.text()
            soup = BeautifulSoup(content, "html.parser")
            results = []
            for scale_period in soup.find_all("div", class_ = "scale_info_periods"):
                isToday = True
                header = scale_period.find("h4", class_ = "scale_info_title")
                if(re.search('завтра', header.text, re.IGNORECASE)):
                    isToday = False

                periods = scale_period.find_all("div", class_="periods_items")
                for period in periods:
                    for item in period.find_all("span"):
                        hours = item.find_all("b")
                        times = []
                        for hour in hours:
                            if(bool(re.match(TIMEPATTERN, hour.text))):
                                print(hour.text)
                                times.append(hour.text)
                        if(len(times)==2):
                            results.append(PowerOffPeriod(int(times[0].split(':')[0]),int(times[0].split(':')[1]),int(times[1].split(':')[0]), int(times[1].split(':')[1]), today=isToday))
                    # results += self.merge_periods(results)
            
            return results

    def _parse_item(self, item: BeautifulSoup) -> tuple[int, int]:
        start_hour = item.find("i", class_="hour_info_from")
        end_hour = item.find("i", class_="hour_info_to")
        if start_hour and end_hour:
            return int(start_hour.text.split(':')[0]), int(end_hour.text.split(':')[0])
        raise ValueError(f"Time period not found in the input string: {item.text}")
