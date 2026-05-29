#!/usr/bin/env python3
import asyncio
from bleak import BleakScanner, BleakClient
from datetime import datetime

# ================= НАСТРОЙКИ =================
DEVICE_NAME = "LTD_000001"
CHARACTERISTIC_UUID = "f000fff1-0451-4000-b000-000000000000"

# Данные для отправки
DATA = bytes([0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0x02, 0x80, 0x00, 0x00, 0x82])

INTERVAL_SECONDS = 20
# ============================================


def bytes_to_hex(data: bytes) -> str:
    """Преобразует bytes в удобный hex-формат"""
    return ' '.join(f'{b:02X}' for b in data)


def notification_handler(sender, data: bytes):
    """Обработчик уведомлений"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] Получено: {bytes_to_hex(data)}")


async def write_to_device(client: BleakClient):
    try:
        await client.write_gatt_char(CHARACTERISTIC_UUID, DATA, response=False)
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] Отправлено: {bytes_to_hex(DATA)}")
        return True
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Ошибка записи: {e}")
        return False


async def main():
    print(f"Запуск BLE скрипта для {DEVICE_NAME}")
    print(f"Период отправки: {INTERVAL_SECONDS} сек | Notify включён\n")

    while True:
        try:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔍 Поиск {DEVICE_NAME}...")

            devices = await BleakScanner.discover(timeout=8.0)
            target_device = next((dev for dev in devices if dev.name == DEVICE_NAME), None)

            if not target_device:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Устройство не найдено. Ожидание {INTERVAL_SECONDS} сек...")
                await asyncio.sleep(INTERVAL_SECONDS)
                continue

            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Устройство найдено: {target_device.address}")

            async with BleakClient(target_device.address) as client:
                print(f"   🔗 Подключено успешно")

                # Включаем уведомления
                await client.start_notify(CHARACTERISTIC_UUID, notification_handler)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🛎️  Notify включён на характеристике")

                # Первая отправка
                await write_to_device(client)

                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏳ Работаем... (отправка каждые {INTERVAL_SECONDS} сек)\n")

                # Бесконечный цикл отправки
                while True:
                    await asyncio.sleep(INTERVAL_SECONDS)
                    await write_to_device(client)

        except asyncio.CancelledError:
            print("\n\nСкрипт остановлен.")
            break
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Ошибка: {e}")
            await asyncio.sleep(INTERVAL_SECONDS)
        finally:
            # Попытка отключить notify при выходе из блока
            if 'client' in locals() and client.is_connected:
                try:
                    await client.stop_notify(CHARACTERISTIC_UUID)
                except:
                    pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСкрипт завершён пользователем.")