#!/usr/bin/env python3
"""
Скрипт для добавления администратора в систему
"""

import os
import sys
from dotenv import load_dotenv

def add_admin():
    """Добавление администратора"""
    print("🔧 Добавление администратора в SFX Savdo Bot")
    print("=" * 50)
    
    # Загружаем текущие настройки
    load_dotenv()
    current_admins = os.getenv('ADMIN_IDS', '')
    
    print(f"Текущие администраторы: {current_admins}")
    print()
    
    # Запрашиваем ID нового администратора
    try:
        new_admin_id = input("Введите ID нового администратора: ").strip()
        
        if not new_admin_id.isdigit():
            print("❌ ID должен быть числом!")
            return
        
        # Формируем новый список администраторов
        admin_list = [admin.strip() for admin in current_admins.split(',') if admin.strip()]
        
        if new_admin_id in admin_list:
            print("⚠️ Этот администратор уже добавлен!")
            return
        
        admin_list.append(new_admin_id)
        new_admin_ids = ','.join(admin_list)
        
        # Обновляем файл .env
        env_content = []
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('ADMIN_IDS='):
                    env_content.append(f'ADMIN_IDS={new_admin_ids}\n')
                else:
                    env_content.append(line)
        
        with open('.env', 'w') as f:
            f.writelines(env_content)
        
        print(f"✅ Администратор {new_admin_id} успешно добавлен!")
        print(f"Новый список администраторов: {new_admin_ids}")
        print()
        print("🔄 Перезапустите бота для применения изменений:")
        print("python run_bot.py")
        
    except KeyboardInterrupt:
        print("\n❌ Операция отменена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def remove_admin():
    """Удаление администратора"""
    print("🗑️ Удаление администратора из SFX Savdo Bot")
    print("=" * 50)
    
    # Загружаем текущие настройки
    load_dotenv()
    current_admins = os.getenv('ADMIN_IDS', '')
    admin_list = [admin.strip() for admin in current_admins.split(',') if admin.strip()]
    
    if not admin_list:
        print("❌ Нет администраторов для удаления!")
        return
    
    print("Текущие администраторы:")
    for i, admin_id in enumerate(admin_list, 1):
        print(f"{i}. {admin_id}")
    
    try:
        choice = input("\nВведите номер администратора для удаления: ").strip()
        
        if not choice.isdigit():
            print("❌ Номер должен быть числом!")
            return
        
        index = int(choice) - 1
        if index < 0 or index >= len(admin_list):
            print("❌ Неверный номер!")
            return
        
        removed_admin = admin_list.pop(index)
        new_admin_ids = ','.join(admin_list)
        
        # Обновляем файл .env
        env_content = []
        with open('.env', 'r') as f:
            for line in f:
                if line.startswith('ADMIN_IDS='):
                    env_content.append(f'ADMIN_IDS={new_admin_ids}\n')
                else:
                    env_content.append(line)
        
        with open('.env', 'w') as f:
            f.writelines(env_content)
        
        print(f"✅ Администратор {removed_admin} удален!")
        print(f"Новый список администраторов: {new_admin_ids}")
        print()
        print("🔄 Перезапустите бота для применения изменений:")
        print("python run_bot.py")
        
    except KeyboardInterrupt:
        print("\n❌ Операция отменена")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def list_admins():
    """Просмотр списка администраторов"""
    print("👥 Список администраторов SFX Savdo Bot")
    print("=" * 50)
    
    # Загружаем текущие настройки
    load_dotenv()
    current_admins = os.getenv('ADMIN_IDS', '')
    admin_list = [admin.strip() for admin in current_admins.split(',') if admin.strip()]
    
    if not admin_list:
        print("❌ Нет администраторов!")
        return
    
    print("Текущие администраторы:")
    for i, admin_id in enumerate(admin_list, 1):
        print(f"{i}. {admin_id}")

def main():
    """Главная функция"""
    print("🔧 Управление администраторами SFX Savdo Bot")
    print("=" * 50)
    print("1. Добавить администратора")
    print("2. Удалить администратора")
    print("3. Просмотреть список администраторов")
    print("4. Выход")
    print()
    
    try:
        choice = input("Выберите действие (1-4): ").strip()
        
        if choice == '1':
            add_admin()
        elif choice == '2':
            remove_admin()
        elif choice == '3':
            list_admins()
        elif choice == '4':
            print("👋 До свидания!")
        else:
            print("❌ Неверный выбор!")
            
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main() 