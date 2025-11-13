import pandas as pd
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class ScenarioApplier:
    """Применяет различные сценарии объединения таблиц"""
    
    @staticmethod
    def apply_scenario_1(old_df: pd.DataFrame, new_df: pd.DataFrame, conflict_rule: str = 'A') -> Tuple[pd.DataFrame, str]:
        """
        Сценарий 1: Сохранить структуру + добавить строки
        - Сохраняет оригинальные столбцы старой таблицы
        - Добавляет новые строки из новой таблицы
        - Игнорирует новые столбцы из новой таблицы
        - Разрешает конфликты имен по выбранному правилу
        """
        logger.info("🔄 Применение сценария 1: Сохранить структуру + добавить строки")
        
        try:
            # Сохраняем структуру старой таблицы
            result_df = old_df.copy()
            
            # Определяем общие столбцы
            common_columns = list(set(old_df.columns) & set(new_df.columns))
            
            if common_columns and 'id' in common_columns:
                # Находим новые строки по id
                old_ids = set(old_df['id'].dropna().astype(int))
                new_ids = set(new_df['id'].dropna().astype(int))
                
                new_row_ids = new_ids - old_ids
                
                if new_row_ids:
                    # Добавляем новые строки
                    new_rows_df = new_df[new_df['id'].isin(new_row_ids)][common_columns].copy()
                    result_df = pd.concat([result_df, new_rows_df], ignore_index=True)
                    
                    # Применяем правило конфликта для существующих строк
                    common_row_ids = old_ids & new_ids
                    if common_row_ids and conflict_rule != 'A' and 'Имя' in common_columns:
                        # Создаем маппинг id -> имя из новой таблицы
                        name_mapping = {}
                        for _, row in new_df.iterrows():
                            if pd.notna(row['id']):
                                row_id = int(row['id'])
                                if 'Имя' in row and pd.notna(row['Имя']):
                                    name_mapping[row_id] = row['Имя']
                        
                        # Обновляем имена в существующих строках
                        for idx in result_df.index:
                            if pd.notna(result_df.at[idx, 'id']):
                                row_id = int(result_df.at[idx, 'id'])
                                if row_id in name_mapping:
                                    if conflict_rule == 'B':
                                        # Полностью заменяем на новые имена
                                        result_df.at[idx, 'Имя'] = name_mapping[row_id]
                                    elif conflict_rule == 'C':
                                        # Приоритет новым именам
                                        result_df.at[idx, 'Имя'] = name_mapping[row_id]
                    
                    message = f"✅ Добавлено {len(new_rows_df)} новых строк"
                else:
                    message = "✅ Новых строк для добавления не найдено"
            else:
                message = "⚠️ Нет общих столбцов для добавления строк"
            
            logger.info(f"✅ Сценарий 1 применен: {message}")
            return result_df, message
            
        except Exception as e:
            logger.error(f"❌ Ошибка в сценарии 1: {e}")
            return old_df, f"❌ Ошибка: {str(e)}"
    
    @staticmethod
    def apply_scenario_2(old_df: pd.DataFrame, new_df: pd.DataFrame, conflict_rule: str = 'A') -> Tuple[pd.DataFrame, str]:
        """
        Сценарий 2: Расширить структуру + сохранить строки
        - Добавляет новые столбцы из новой таблицы
        - Сохраняет все строки из старой таблицы
        - Не добавляет новые строки из новой таблицы
        - Разрешает конфликты имен по выбранному правилу
        """
        logger.info("🔄 Применение сценария 2: Расширить структуру + сохранить строки")
        
        try:
            # Начинаем со старой таблицы
            result_df = old_df.copy()
            
            # Добавляем новые столбцы из новой таблицы
            new_columns = list(set(new_df.columns) - set(old_df.columns))
            for col in new_columns:
                result_df[col] = None
            
            # Определяем общие столбцы
            common_columns = list(set(old_df.columns) & set(new_df.columns))
            
            if common_columns and 'id' in common_columns:
                # Заполняем новые столбцы данными из новой таблицы
                for idx in result_df.index:
                    if pd.notna(result_df.at[idx, 'id']):
                        row_id = int(result_df.at[idx, 'id'])
                        
                        # Находим соответствующую строку в новой таблице
                        matching_rows = new_df[new_df['id'] == row_id]
                        if not matching_rows.empty:
                            matching_row = matching_rows.iloc[0]
                            
                            # Заполняем новые столбцы
                            for col in new_columns:
                                if col in matching_row and pd.notna(matching_row[col]):
                                    result_df.at[idx, col] = matching_row[col]
                            
                            # Применяем правило конфликта для имен
                            if 'Имя' in common_columns and conflict_rule != 'A':
                                if 'Имя' in matching_row and pd.notna(matching_row['Имя']):
                                    if conflict_rule == 'B':
                                        # Полностью заменяем на новые имена
                                        result_df.at[idx, 'Имя'] = matching_row['Имя']
                                    elif conflict_rule == 'C':
                                        # Приоритет новым именам
                                        result_df.at[idx, 'Имя'] = matching_row['Имя']
            
            message = f"✅ Добавлено {len(new_columns)} новых столбцов"
            logger.info(f"✅ Сценарий 2 применен: {message}")
            return result_df, message
            
        except Exception as e:
            logger.error(f"❌ Ошибка в сценарии 2: {e}")
            return old_df, f"❌ Ошибка: {str(e)}"
    
    @staticmethod
    def apply_scenario_3(old_df: pd.DataFrame, new_df: pd.DataFrame, conflict_rule: str = 'A') -> Tuple[pd.DataFrame, str]:
        """
        Сценарий 3: Полное объединение (структура + строки)
        - Добавляет новые столбцы из новой таблицы
        - Добавляет новые строки из новой таблицы
        - Сохраняет все строки из старой таблицы
        - Разрешает конфликты имен по выбранному правилу
        """
        logger.info("🔄 Применение сценария 3: Полное объединение")
        
        try:
            # Создаем полный набор столбцов
            all_columns = list(set(old_df.columns) | set(new_df.columns))
            
            # Создаем пустой DataFrame с правильными столбцами
            result_df = pd.DataFrame(columns=all_columns)
            
            # Сначала добавляем все данные из старой таблицы
            for col in old_df.columns:
                if col in result_df.columns:
                    result_df[col] = old_df[col]
                else:
                    result_df[col] = None
            
            # Добавляем недостающие столбцы и заполняем их
            for col in new_df.columns:
                if col not in result_df.columns:
                    result_df[col] = None
            
            # Определяем общие столбцы
            common_columns = list(set(old_df.columns) & set(new_df.columns))
            
            if common_columns and 'id' in common_columns:
                # Находим id из обеих таблиц
                old_ids = set(old_df['id'].dropna().astype(int))
                new_ids = set(new_df['id'].dropna().astype(int))
                
                # Обновляем данные из новой таблицы для существующих строк
                for idx in result_df.index:
                    if pd.notna(result_df.at[idx, 'id']):
                        row_id = int(result_df.at[idx, 'id'])
                        
                        # Находим соответствующую строку в новой таблице
                        matching_rows = new_df[new_df['id'] == row_id]
                        if not matching_rows.empty:
                            matching_row = matching_rows.iloc[0]
                            
                            # Обновляем все столбцы из новой таблицы
                            for col in new_df.columns:
                                if col in result_df.columns and pd.notna(matching_row[col]):
                                    # Применяем правило конфликта для имен
                                    if col == 'Имя' and conflict_rule != 'A':
                                        if conflict_rule == 'B':
                                            # Полностью заменяем на новые имена
                                            result_df.at[idx, col] = matching_row[col]
                                        elif conflict_rule == 'C':
                                            # Приоритет новым именам
                                            result_df.at[idx, col] = matching_row[col]
                                    else:
                                        # Для остальных столбцов просто заполняем
                                        result_df.at[idx, col] = matching_row[col]
                
                # Добавляем новые строки из новой таблицы
                new_row_ids = new_ids - old_ids
                if new_row_ids:
                    new_rows_data = []
                    
                    for row_id in new_row_ids:
                        # Находим строку в новой таблице
                        matching_rows = new_df[new_df['id'] == row_id]
                        if not matching_rows.empty:
                            matching_row = matching_rows.iloc[0]
                            
                            # Создаем новую строку с данными из новой таблицы
                            new_row = {}
                            for col in all_columns:
                                if col in matching_row and pd.notna(matching_row[col]):
                                    new_row[col] = matching_row[col]
                                else:
                                    new_row[col] = None
                            
                            new_rows_data.append(new_row)
                    
                    if new_rows_data:
                        new_rows_df = pd.DataFrame(new_rows_data)
                        result_df = pd.concat([result_df, new_rows_df], ignore_index=True)
            
            # Упорядочиваем столбцы для лучшего отображения
            preferred_order = ['id', 'Имя', 'Фамилия'] + [col for col in all_columns if col not in ['id', 'Имя', 'Фамилия']]
            existing_columns = [col for col in preferred_order if col in result_df.columns]
            result_df = result_df[existing_columns]
            
            message = f"✅ Полное объединение: {len(result_df)} строк, {len(result_df.columns)} столбцов"
            logger.info(f"✅ Сценарий 3 применен: {message}")
            return result_df, message
            
        except Exception as e:
            logger.error(f"❌ Ошибка в сценарии 3: {e}")
            return old_df, f"❌ Ошибка: {str(e)}"
    
    @staticmethod
    def apply_scenario_4(old_df: pd.DataFrame, new_df: pd.DataFrame, conflict_rule: str = 'A') -> Tuple[pd.DataFrame, str]:
        """
        Сценарий 4: Умное объединение (автоматический выбор)
        - Автоматический выбор оптимальной стратегии
        - Анализирует объем изменений и предлагает баланс
        """
        logger.info("🔄 Применение сценария 4: Умное объединение")
        
        try:
            # Анализируем различия между таблицами
            old_cols = set(old_df.columns)
            new_cols = set(new_df.columns)
            
            added_cols = len(new_cols - old_cols)
            
            # Анализируем строки по id
            if 'id' in old_df.columns and 'id' in new_df.columns:
                old_ids = set(old_df['id'].dropna().astype(int))
                new_ids = set(new_df['id'].dropna().astype(int))
                added_rows = len(new_ids - old_ids)
            else:
                added_rows = len(new_df)
            
            # Эвристика для выбора сценария
            if added_cols >= 2 and added_rows >= 2:
                # Много новых столбцов и строк - полное объединение
                result_df, message = ScenarioApplier.apply_scenario_3(old_df, new_df, conflict_rule)
                message = f"⚡ Умное объединение (полное): {message}"
            elif added_cols > added_rows:
                # Больше новых столбцов - расширяем структуру
                result_df, message = ScenarioApplier.apply_scenario_2(old_df, new_df, conflict_rule)
                message = f"⚡ Умное объединение (расширение): {message}"
            else:
                # Больше новых строк или баланс - добавляем строки
                result_df, message = ScenarioApplier.apply_scenario_1(old_df, new_df, conflict_rule)
                message = f"⚡ Умное объединение (добавление строк): {message}"
            
            logger.info(f"✅ Сценарий 4 применен: {message}")
            return result_df, message
            
        except Exception as e:
            logger.error(f"❌ Ошибка в сценарии 4: {e}")
            return old_df, f"❌ Ошибка: {str(e)}"
    
    @staticmethod
    def apply_scenario(scenario: str, old_df: pd.DataFrame, new_df: pd.DataFrame, conflict_rule: str = 'A') -> Tuple[pd.DataFrame, str]:
        """Применяет выбранный сценарий"""
        scenarios = {
            '1': ScenarioApplier.apply_scenario_1,
            '2': ScenarioApplier.apply_scenario_2,
            '3': ScenarioApplier.apply_scenario_3,
            '4': ScenarioApplier.apply_scenario_4
        }
        
        if scenario in scenarios:
            return scenarios[scenario](old_df, new_df, conflict_rule)
        else:
            logger.error(f"❌ Неизвестный сценарий: {scenario}")
            return old_df, f"❌ Неизвестный сценарий: {scenario}"
