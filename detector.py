import subprocess
import cv2
import requests
import yaml
import fake_useragent
import numpy as np
from time import sleep, time
import asyncio
from math import radians, cos, sin, asin, sqrt


prev = None
user_agent = fake_useragent.UserAgent()['google chrome']
headers = {'user-agent': user_agent, 'if-none-match': "2979-3kcziSj429jfGMhljZ/o5eCq/7E", 'referer': 'https://nycpokemap.com/', 'authority': 'nycpokemap.com', 'x-requested-with': 'XMLHttpRequest'}
url = 'https://nycpokemap.com/pokestop.php?time='
needed, already = [24, 25, 12, 13, 16, 17], []


class MainAction():
    def __init__(self):
        with open('config.yaml', "r") as f:
            self.config = yaml.load(f)
            self.device_id = ''
    
    async def run(self, args):
        subprocess.Popen([str(x) for x in args]).communicate()

    async def get_devices(self):
        p = subprocess.Popen('adb devices'.split(' '), stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()
        devices = []

        for line in stdout.decode('utf-8').splitlines()[1:-1]:
            device_id, name = line.split('\t')
            devices.append(device_id)

        return devices

    async def get_device(self):
        devices = await self.get_devices()
        if len(devices) == 1:
            return devices
        print('Choose your device from the list:')
        print('0: choose all devices')
        for i in range(0, len(devices)):
            print(f'{i + 1}: {devices[i]}')
        ans = int(input())
        if ans == 0:
            return devices
        return [devices[ans - 1]]

    async def click(self, location):
        await self.run(f"adb -s {self.device_id} shell input tap {location[0]} {location[1]}".split(' '))

    async def gotcha(self, device_id):
        await self.click(self.config[self.device_id]['teleport_plus_gotcha_locations']['open_teleport'])
        sleep(1)
        await self.click(self.config[self.device_id]['teleport_plus_gotcha_locations']['paste_cords'])
        sleep(1)
        await self.click(self.config[self.device_id]['teleport_plus_gotcha_locations']['teleport'])
        sleep(1)
        await pyautogui.moveTo(self.config[self.device_id]['teleport_plus_gotcha_locations']['pre_throw'])
        sleep(0.5)
        await pyautogui.dragTo(self.config[self.device_id]['teleport_plus_gotcha_locations']['throw'])
        sleep(1.5)
    
    async def reopen(self, device_id):
        await self.run(f'adb -s {self.device_id} shell am force-stop com.nianticlabs.pokemongo'.split(' '))
        sleep(2)
        await self.run(f'adb -s {self.device_id} shell am start -n com.pokemod.hal.public/com.pokemod.hal.ui.activities.AuthActivity'.split(' '))
        sleep(2)
        await self.click(self.config[self.device_id]['reopen_locations']['start_service_button'])
        sleep(1)
        await self.click(self.config[self.device_id]['reopen_locations']['start_service_button'])
        sleep(40)
        await self.click(self.config[self.device_id]['reopen_locations']['close_all_trashnews'])
        sleep(0.5)
        await self.click(self.config[self.device_id]['reopen_locations']['close_all_trashnews'])
        sleep(0.5)
        await self.click(self.config[self.device_id]['reopen_locations']['close_all_trashnews'])
        await self.swipe(
            (
                self.config[device_id]['reopen_locations']['close_all_trashnews']
            ),
            (
                self.config[device_id]['reopen_locations']['close_all_trashnews'][0],
                self.config[device_id]['reopen_locations']['close_all_trashnews'][1] + 300
            ),
            duration=250,
        )
        await self.click(self.config[self.device_id]['reopen_locations']['close_all_trashnews'])
        await self.swipe(
            (
                self.config[self.device_id]['reopen_locations']['close_all_trashnews']
            ),
            (
                self.config[self.device_id]['reopen_locations']['close_all_trashnews'][0],
                self.config[self.device_id]['reopen_locations']['close_all_trashnews'][1] + 300
            ),
            duration=250,
        )

    async def open_backpack(self):
        await self.click(self.config[self.device_id]['locations']['backpack_icon'])
        sleep(1)
        await self.click(self.config[self.device_id]['locations']['close_backpack_icon'])
        sleep(1)
        await self.click(self.config[self.device_id]['locations']['close_backpack_icon'])

    async def open_stop(self):
        await self.click(self.config[self.device_id]['locations']['open_pokestop'])
    
    async def close_pokestop(self):
        await self.click(self.config[self.device_id]['locations']['close_pokestop'])
    
    async def exit_pokemon(self):
        await self.click(self.config[self.device_id]['locations']['exit_pokemon'])
    
    async def swipe(self, start_point, target_point, duration=None):
        await self.run(f"adb -s {self.device_id} shell input swipe {start_point[0]} {start_point[1]} {target_point[0]} {target_point[1]} {duration}".split(' '))

    async def make_screencap(self):
        while True:
            await self.run(["adb", "-s", self.device_id, "shell", "screencap", "-p", "/sdcard/screen.png"])
            await self.run(["adb", "-s", self.device_id, "pull", "/sdcard/screen.png", "."])
            await asyncio.sleep(1)

    async def crop_img(self, img, cords):
        x, y, w, h = cords
        return img[y:y+h, x:x+w]

    async def get_invasion(self):
        global prev
        cords = []
        ans = []
        data = requests.get(url=url, headers=headers).json()
        for i in range(len(data['invasions'])):
            if int(data['invasions'][i]['invasion_end']) - data['meta']['time'] > 300 and int(data['invasions'][i]['character']) in needed and (data['invasions'][i]['lat'], data['invasions'][i]['lng']) not in already:
                cords.append(((data['invasions'][i]['lat'], data['invasions'][i]['lng']), int(data['invasions'][i]['character'])))

        if prev == None:
            coordinates = f'{cords[0][0][0]},{cords[0][0][1]}'
            prev = (cords[0][0][0], cords[0][0][1])
        else:
            for i in cords:
                dist = await haversine(float(prev[0]), float(prev[1]), float(i[0][0]), float(i[0][1]))
                ans.append((dist, i[0][0], i[0][1], i[1]))
            
            ans.sort(key=lambda x: x[0])
            ans = ans[:1][0]
            coordinates = f'{ans[1]},{ans[2]}'
            prev = (ans[1], ans[2])

        await self.run(f'adb -s {self.device_id} shell am start -a android.intent.action.VIEW -d "https://pk.md/{coordinates}"'.split(' '))
        already.append(prev)
    
    async def get_done_screen(self):
        return cv2.imread('screen.png')

async def haversine(lat1, lon1, lat2, lon2):
    lon1, lat1, lon2, lat2 = map(radians, (lon1, lat1, lon2, lat2))

    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    km = 6367 * c
    return km


