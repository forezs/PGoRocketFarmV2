from detector import *

device_id = ''
end = False
action = MainAction()
devices = None
count = -1

async def change_device_priority():
        global devices, limit, count
        if not devices:
            device_list = await action.get_device()
            devices = device_list
            limit = len(devices) - 1

        count += 1
        detector.device_id = devices[count]
        action.device_id = devices[count]
        detector.team_r = cv2.imread(detector.device_id + '/' + 'r_detect.png', cv2.IMREAD_GRAYSCALE)
        detector.team_r_2 = cv2.imread(detector.device_id + '/' + 'r_detect_2.png', cv2.IMREAD_GRAYSCALE)
        detector.stop = cv2.imread(detector.device_id + '/' + 'stop.png', cv2.IMREAD_GRAYSCALE)
        detector.conf = cv2.imread(detector.device_id + '/' + 'confirm.png', cv2.IMREAD_GRAYSCALE)
        detector.poke = cv2.imread(detector.device_id + '/' + 'poke.png', cv2.IMREAD_GRAYSCALE)
        print()
        print(f'working on: {action.device_id}...')
        if count == limit:
            count = -1
        await asyncio.sleep(2)


class MainDetector:
    def __init__(self):
        self.device_id = ''
        self.team_r = cv2.imread(self.device_id + '/' + 'r_detect.png', cv2.IMREAD_GRAYSCALE)
        self.team_r_2 = cv2.imread(self.device_id + '/' + 'r_detect_2.png', cv2.IMREAD_GRAYSCALE)
        self.stop = cv2.imread(self.device_id + '/' + 'stop.png', cv2.IMREAD_GRAYSCALE)
        self.conf = cv2.imread(self.device_id + '/' + 'confirm.png', cv2.IMREAD_GRAYSCALE)
        self.poke = cv2.imread(self.device_id + '/' + 'poke.png', cv2.IMREAD_GRAYSCALE)

    async def open_pokestop(self):
        while True:
            global end_time
            end_time = time()
            stop_img = await action.crop_img(await action.get_done_screen(), action.config[self.device_id]['locations']['open_pokestop_area'])

            capture = cv2.cvtColor(stop_img, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(capture, self.team_r, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= 0.35)

            if loc[::-1][1].size > 0:
                await action.open_stop()
                print('[INFO] POKESTOP OPENED')
                sleep(1)
                await asyncio.sleep(3)

            capture = cv2.cvtColor(stop_img, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(capture, self.team_r_2, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= 0.35)

            if loc[::-1][1].size > 0:
                await action.open_stop()
                print('[INFO] POKESTOP OPENED')
                sleep(1)
                await asyncio.sleep(3)
            await asyncio.sleep(1)

    async def close_pokestop(self):
        while True:
            close_img = await action.crop_img(await action.get_done_screen(), action.config[self.device_id]['locations']['pokestop_more_button_area'])

            capture = cv2.cvtColor(close_img, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(capture, self.stop, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= 0.75)

            if loc[::-1][1].size > 0:
                await action.close_pokestop()
                print('[INFO] POKESTOP CLOSED')
                await asyncio.sleep(5)
            await asyncio.sleep(1)

    async def battle(self):
        while True:
            battle_img = await action.crop_img(await action.get_done_screen(), action.config[self.device_id]['locations']['use_this_party_area'])

            capture = cv2.cvtColor(battle_img, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(capture, self.conf, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= 0.75)

            if loc[::-1][1].size > 0:
                await action.open_backpack()
                await asyncio.sleep(5)
            await asyncio.sleep(60)

    async def detect_poke(self):
        while True:
            exit_img = await action.crop_img(await action.get_done_screen(), action.config[self.device_id]['locations']['berry_encounter_area'])

            capture = cv2.cvtColor(exit_img, cv2.COLOR_BGR2GRAY)
            res = cv2.matchTemplate(capture, self.poke, cv2.TM_CCOEFF_NORMED)
            loc = np.where(res >= 0.75)
     
            if loc[::-1][1].size > 0:
                await action.exit_pokemon()
                print('[INFO] ROCKET BEATEN')
                await action.get_invasion()
            await change_device_priority()
            await asyncio.sleep(1)

detector = MainDetector()



async def main():
    await change_device_priority()
    for _ in devices:
        await change_device_priority()
        print(action.device_id)
        await action.get_invasion()

    await asyncio.gather(
        action.make_screencap(),
        detector.open_pokestop(),
        detector.close_pokestop(),
        detector.battle(),
        detector.detect_poke()
    )


if __name__ == '__main__':
    asyncio.run(main())