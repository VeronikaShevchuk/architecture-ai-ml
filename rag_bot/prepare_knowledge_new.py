import re
import os
import json
import shutil
from pathlib import Path
import pymorphy2

class FictionalTextReplacer:
    def __init__(self, mapping_config):
        """
        Инициализация класса с конфигурацией замен
        """
        self.config = mapping_config
        self.morph = pymorphy2.MorphAnalyzer(lang='ru')
        self.terms_mapping = self.config['terms_mapping']
        self.filename_mapping = {}
        
        # Создаем маппинг для имен файлов
        self._create_filename_mapping()
        
        # Создаем расширенный словарь для замен с учетом всех форм
        self.expanded_mapping = self._expand_mapping()
        
        # Компилируем паттерны
        self.compiled_patterns = self._compile_patterns()
    
    def _create_filename_mapping(self):
        """
        Создание маппинга для имен файлов
        """
        filename_map = {
            "Мастер": "Архивариус",
            "Маргарита": "Королева Розы",
            "Воланд": "Магистр Теней",
            "Берлиоз": "Меркурий",
            "Иван Бездомный": "Поэт Искандер",
            "Понтий Пилат": "Прокуратор Север",
            "Иешуа": "Странник Рассвет",
            "Москва": "Град Семи Холмов",
            "Коровьев": "Шут Фантом",
            "Бегемот": "Плут",
            "Азазелло": "Морок",
            "Гелла": "Мгла",
            "Аннушка": "Неуклюжая"
        }
        self.filename_mapping = filename_map
    
    def _get_all_forms(self, word):
        """
        Получение всех возможных форм слова
        """
        try:
            parsed = self.morph.parse(word)[0]
            forms = set()
            
            # Получаем все возможные падежи
            cases = ['nomn', 'gent', 'datv', 'accs', 'ablt', 'loct']
            numbers = ['sing', 'plur']
            
            for case in cases:
                for number in numbers:
                    try:
                        inflected = parsed.inflect({case, number})
                        if inflected:
                            forms.add(inflected.word)
                    except:
                        continue
            
            # Добавляем исходное слово
            forms.add(word.lower())
            
            return list(forms)
        except:
            return [word]
    
    def _expand_mapping(self):
        """
        Расширение словаря замен с учетом всех форм слов
        """
        expanded = {}
        
        # Составные термины (обрабатываются отдельно)
        compound_terms = {
            "Иван Бездомный": "Поэт Искандер",
            "Понтий Пилат": "Прокуратор Север",
            "Иешуа Га-Ноцри": "Странник Рассвет",
            "Михаил Берлиоз": "Идеолог Меркурий",
            "Степа Лиходеев": "Балагур Лиходей",
            "Нехорошая квартира": "Палата Призраков",
            "Патриаршие пруды": "Парк Встреч",
            "Дом Грибоедова": "Храм Искусств",
            "Клиника Стравинского": "Обитель Покоя",
            "Лысая гора": "Вершина Теней",
            "Роман Мастера": "Свиток Судеб",
            "Свита Воланда": "Сумеречный Легион",
            "Великий бал у сатаны": "Ночь Откровений",
            "Крем Азазелло": "Эликсир Превращений",
            "Чёрный пудель": "Пес Теней",
            "Пятиконечная свеча": "Звездный Огонь",
            "Воландова свита": "Свита Теней"
        }
        
        # Добавляем составные термины
        for compound, replacement in compound_terms.items():
            expanded[compound.lower()] = replacement
        
        # Добавляем отдельные слова со всеми формами
        for original, replacement in self.terms_mapping.items():
            if original not in [word for compound in compound_terms.keys() for word in compound.split()]:
                forms = self._get_all_forms(original)
                for form in forms:
                    expanded[form.lower()] = replacement
        
        return expanded
    
    def _compile_patterns(self):
        """
        Создание паттернов для поиска
        """
        patterns = []
        
        # Сортируем по длине (сначала длинные фразы)
        sorted_terms = sorted(self.expanded_mapping.keys(), key=len, reverse=True)
        
        for term in sorted_terms:
            replacement = self.expanded_mapping[term]
            
            # Экранируем специальные символы
            pattern = re.escape(term)
            
            # Добавляем границы слова
            pattern = r'\b' + pattern + r'\b'
            
            patterns.append({
                'pattern': re.compile(pattern, re.IGNORECASE),
                'replacement': replacement,
                'original': term
            })
        
        return patterns
    
    def _get_replacement_with_case(self, original_word, replacement):
        """
        Применение правильного регистра к замене
        """
        if original_word.isupper():
            return replacement.upper()
        elif original_word.istitle():
            return replacement.title()
        else:
            return replacement.lower()
    
    def replace_text(self, text):
        """
        Замена всех вхождений в тексте
        """
        result = text
        
        # Сначала обрабатываем все паттерны
        for pattern_info in self.compiled_patterns:
            pattern = pattern_info['pattern']
            replacement_base = pattern_info['replacement']
            
            def replace_with_case(match):
                original_word = match.group(0)
                return self._get_replacement_with_case(original_word, replacement_base)
            
            result = pattern.sub(replace_with_case, result)
        
        # Дополнительная проверка для проблемных случаев
        # Замена для "Патриарших прудов"
        result = re.sub(
            r'Патриарших\s+прудов',
            'Парка Встреч',
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(
            r'Патриаршие\s+пруды',
            'Парк Встреч',
            result,
            flags=re.IGNORECASE
        )
        
        # Замена для "нехорошей квартире"
        result = re.sub(
            r'нехорошей\s+квартире',
            'Палате Призраков',
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(
            r'нехорошая\s+квартира',
            'Палата Призраков',
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(
            r'нехорошую\s+квартиру',
            'Палату Призраков',
            result,
            flags=re.IGNORECASE
        )
        result = re.sub(
            r'нехорошей\s+квартиры',
            'Палаты Призраков',
            result,
            flags=re.IGNORECASE
        )
        
        # Замена для "Берлиоз"
        result = re.sub(
            r'Берлиоз\w*',
            'Меркурий',
            result,
            flags=re.IGNORECASE
        )
        
        # Замена для "Неуклюжая" (Аннушка)
        result = re.sub(
            r'Аннушк\w*',
            'Неуклюжая',
            result,
            flags=re.IGNORECASE
        )
        
        return result
    
    def get_new_filename(self, original_filename):
        """
        Генерация нового имени файла
        """
        new_filename = original_filename
        
        for old_word, new_word in self.filename_mapping.items():
            if old_word in new_filename:
                new_filename = new_filename.replace(old_word, new_word)
        
        return new_filename
    
    def process_file(self, input_path, output_dir):
        """
        Обработка одного файла
        """
        try:
            with open(input_path, 'r', encoding='utf-8') as f:
                text = f.read()
            
            # Заменяем название мира
            if self.config.get('original_world') and self.config.get('fictional_world'):
                text = text.replace(self.config['original_world'], self.config['fictional_world'])
            
            # Применяем все замены
            processed_text = self.replace_text(text)
            
            # Генерируем новое имя файла
            original_filename = Path(input_path).name
            new_filename = self.get_new_filename(original_filename)
            
            # Создаем путь для сохранения
            relative_path = Path(input_path).relative_to(self.input_directory)
            output_path = Path(output_dir) / relative_path.parent / new_filename
            
            # Создаем директорию
            os.makedirs(output_path.parent, exist_ok=True)
            
            # Сохраняем результат
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed_text)
            
            print(f"✅ Файл обработан: {original_filename} -> {new_filename}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Ошибка при обработке файла {input_path}: {e}")
            return None
    
    def process_directory(self, input_dir, output_dir, extensions=['.txt', '.md']):
        """
        Обработка всех файлов в директории
        """
        self.input_directory = input_dir
        input_path = Path(input_dir)
        
        if not input_path.exists():
            print(f"❌ Директория не существует: {input_dir}")
            return [], []
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        processed_files = []
        copied_files = []
        
        for file_path in input_path.rglob('*'):
            if file_path.is_file():
                if file_path.suffix.lower() in extensions:
                    result = self.process_file(str(file_path), output_dir)
                    if result:
                        processed_files.append(result)
                else:
                    relative_path = file_path.relative_to(input_path)
                    dest_path = output_path / relative_path
                    os.makedirs(dest_path.parent, exist_ok=True)
                    shutil.copy2(str(file_path), str(dest_path))
                    copied_files.append(str(dest_path))
                    print(f"📄 Файл скопирован: {relative_path}")
        
        return processed_files, copied_files


def load_terms_map(config_path):
    """
    Загрузка конфигурации замен из JSON файла
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_fields = ['original_world', 'fictional_world', 'terms_mapping']
        missing_fields = [field for field in required_fields if field not in config]
        
        if missing_fields:
            print(f"❌ В файле конфигурации отсутствуют поля: {', '.join(missing_fields)}")
            return None
        
        print(f"✅ Конфигурация загружена из {config_path}")
        return config
        
    except FileNotFoundError:
        print(f"❌ Файл конфигурации не найден: {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка в JSON файле: {e}")
        return None


def create_sample_config():
    """
    Создание примера файла конфигурации
    """
    sample_config = {
        "original_world": "Мастер и Маргарита",
        "fictional_world": "Хроники Сумеречного Легиона",
        "terms_mapping": {
            "Воланд": "Магистр Теней",
            "Мастер": "Архивариус",
            "Маргарита": "Королева Розы",
            "Коровьев": "Шут Фантом",
            "Бегемот": "Демон-кот Плут",
            "Азазелло": "Палач Морок",
            "Гелла": "Нимфа Мгла",
            "Иван Бездомный": "Поэт Искандер",
            "Понтий Пилат": "Прокуратор Север",
            "Иешуа Га-Ноцри": "Странник Рассвет",
            "Михаил Берлиоз": "Идеолог Меркурий",
            "Степа Лиходеев": "Балагур Лиходей",
            "Москва": "Град Семи Холмов",
            "Нехорошая квартира": "Палата Призраков",
            "Варьете": "Театр Иллюзий",
            "Патриаршие пруды": "Парк Встреч",
            "Дом Грибоедова": "Храм Искусств",
            "Клиника Стравинского": "Обитель Покоя",
            "Ершалаим": "Древний Град",
            "Лысая гора": "Вершина Теней",
            "Роман Мастера": "Свиток Судеб",
            "Свита Воланда": "Сумеречный Легион",
            "Великий бал у сатаны": "Ночь Откровений",
            "Крем Азазелло": "Эликсир Превращений",
            "МАССОЛИТ": "Гильдия Пера",
            "Чёрный пудель": "Пес Теней",
            "Подкова": "Дар Удачи",
            "Пятиконечная свеча": "Звездный Огонь",
            "Беспокойные": "Неупокоенные",
            "Воландова свита": "Свита Теней",
            "Аннушка": "Неуклюжая"
        }
    }
    
    with open('terms_map.json', 'w', encoding='utf-8') as f:
        json.dump(sample_config, f, ensure_ascii=False, indent=2)
    
    print("📄 Создан файл-образец terms_map.json")


def save_processing_log(output_directory, config_path, input_directory, processed_files, copied_files):
    """
    Сохранение лога обработки
    """
    log_data = {
        "input_directory": input_directory,
        "output_directory": output_directory,
        "config_used": config_path,
        "processed_date": "2026-02-27",
        "files_processed": len(processed_files),
        "files_copied": len(copied_files),
        "status": "completed"
    }
    
    log_file = os.path.join(output_directory, "processing_log.json")
    with open(log_file, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)
    
    print(f"📝 Лог обработки сохранен: {log_file}")


def test_replacement():
    """
    Тестовая функция для проверки замен
    """
    config = {
        "original_world": "Мастер и Маргарита",
        "fictional_world": "Хроники Сумеречного Легиона",
        "terms_mapping": {
            "Аннушка": "Неуклюжая",
            "Берлиоз": "Меркурий",
            "Патриаршие пруды": "Парк Встреч",
            "Нехорошая квартира": "Палата Призраков"
        }
    }
    
    replacer = FictionalTextReplacer(config)
    
    test_text = """Неуклюжая — женщина, которая разлила подсолнечное масло на трамвайных путях у Патриарших прудов. Именно из-за этого масла Берлиоз поскользнулся и попал под трамвай. Неуклюжая становится символом роковой случайности. Позже она появляется в нехорошей квартире, пытаясь купить вещи после исчезновения жильцов."""
    
    print("ИСХОДНЫЙ ТЕКСТ:")
    print(test_text)
    print("\n" + "="*50 + "\n")
    
    result = replacer.replace_text(test_text)
    
    print("ТЕКСТ ПОСЛЕ ЗАМЕНЫ:")
    print(result)


def main():
    # Тестируем замену
    test_replacement()
    
    # Путь к файлу конфигурации
    config_path = "terms_map.json"
    
    # Проверяем существование файла конфигурации
    if not os.path.exists(config_path):
        print("⚠️ Файл terms_map.json не найден!")
        create_sample_config()
        return
    
    # Загружаем конфигурацию
    config = load_terms_map(config_path)
    if config is None:
        print("❌ Не удалось загрузить конфигурацию")
        return
    
    # Пути к директориям
    input_directory = "original_texts"
    output_directory = "knowledge_base"
    
    print(f"\n📁 Исходная директория: {input_directory}")
    print(f"📁 Целевая директория: {output_directory}")
    
    # Проверяем существование исходной директории
    if not os.path.exists(input_directory):
        print(f"❌ Директория '{input_directory}' не найдена!")
        os.makedirs(input_directory, exist_ok=True)
        print(f"✅ Директория создана")
        return
    
    # Создаем экземпляр заменятеля
    replacer = FictionalTextReplacer(config)
    
    # Обрабатываем файлы
    processed_files, copied_files = replacer.process_directory(
        input_directory, 
        output_directory, 
        extensions=['.txt', '.md', '.html', '.rtf']
    )
    
    # Сохраняем лог
    save_processing_log(output_directory, config_path, input_directory, processed_files, copied_files)
    
    print(f"\n✨ Обработка завершена!")


if __name__ == "__main__":
    # Проверяем наличие pymorphy2
    try:
        import pymorphy2
    except ImportError:
        print("⚠️ Не установлена библиотека pymorphy2")
        print("   Установите: pip install pymorphy2 pymorphy2-dicts-ru")
        exit(1)
    
    main()