import pandas as pd
import logging
from typing import Dict, Any, Tuple, List

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
            result_df = old_df.copy()
            
            # Определяем общие столбцы для объединения
            common_columns = list(set(old_df.columns) & set(new_df.columns))
            
            if common_columns:
                # Находим новые строки (которые отсутствуют в старой таблице)
                old_combined = old_df[common_columns].fillna('').astype(str).sum(axis=1)
                new_combined = new_df[common_columns].fillna('').astype(str).sum(axis=1)
                
                old_hashes = set(old_combined)
                new_hashes = set(new_combined)
                
                new_rows_hashes = new_hashes - old_hashes
                new_rows_mask = new_combined.isin(new_rows_hashes)
                
                if new_rows_mask.any():
                    # Берем только общие столбцы из новых строк
                    new_rows_df = new_df.loc[new_rows_mask, common_columns].copy()
                    
                    # Применяем правило конфликта для имен в СУЩЕСТВУЮЩИХ строках
                    if 'Имя' in common_columns and conflict_rule != 'A':
                        # Для существующих строк, которые есть в обеих таблицах
                        common_rows_hashes = old_hashes & new_hashes
                        common_rows_mask = new_combined.isin(common_rows_hashes)
                        
                        if common_rows_mask.any():
                            common_new_rows = new_df.loc[common_rows_mask]
                            
                            # Создаем маппинг id -> имя из новой таблицы
                            name_mapping = {}
                            if 'id' in common_columns:
                                for _, row in common_new_rows.iterrows():
                                    name_mapping[row['id']] = row['Имя']
                            
                            # Обновляем имена в существующих строках result_df
                            for idx in result_df.index:
                                row_id = result_df.at[idx, 'id']
                                if row_id in name_mapping:
                                    if conflict_rule == 'B':
                                        # Полностью заменяем на новые имена
                                        result_df.at[idx, 'Имя'] = name_mapping[row_id]
                                    elif conflict_rule == 'C':
                                        # Приоритет новым именам
                                        result_df.at[idx, 'Имя'] = name_mapping[row_id]
                    
                    result_df = pd.concat([result_df, new_rows_df], ignore_index=True)
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
            result_df = old_df.copy()
            
            # Добавляем новые столбцы из новой таблицы
            new_columns = list(set(new_df.columns) - set(old_df.columns))
            
            for col in new_columns:
                result_df[col] = None  # Инициализируем новые столбцы пустыми значениями
            
            # Определяем общие столбцы
            common_columns = list(set(old_df.columns) & set(new_df.columns))
            
            if common_columns and 'id' in common_columns:
                # Создаем словарь для быстрого доступа к данным новой таблицы по id
                new_data_by_id = {}
                for _, row in new_df.iterrows():
                    row_id = row['id']
                    new_data_by_id[row_id] = row
                
                # Заполняем данные из новой таблицы
                for idx in result_df.index:
                    row_id = result_df.at[idx, 'id']
                    if row_id in new_data_by_id:
                        new_row = new_data_by_id[row_id]
                        
                        # Заполняем новые столбцы
                        for col in new_columns:
                            if col in new_row and pd.notna(new_row[col]):
                                result_df.at[idx, col] = new_row[col]
                        
                        # Применяем правило конфликта для имен
                        if 'Имя' in common_columns and conflict_rule != 'A':
                            if 'Имя' in new_row and pd.notna(new_row['Имя']):
                                if conflict_rule == 'B':
                                    # Полностью заменяем на новые имена
                                    result_df.at[idx, 'Имя'] = new_row['Имя']
                                elif conflict_rule == 'C':
                                    # Приоритет новым именам
                                    result_df.at[idx, 'Имя'] = new_row['Имя']
            
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
            result_df = pd.DataFrame(columns=all_columns)
            
            # Сначала добавляем все данные из старой таблицы
            for col in old_df.columns:
                result_df[col] = old_df[col]
            
            # Добавляем новые столбцы и заполняем их
            new_columns = list(set(new_df.columns) - set(old_df.columns))
            for col in new_columns:
                if col not in result_df.columns:
                    result_df[col] = None
            
            # Создаем словарь для быстрого доступа к данным новой таблицы по id
            new_data_by_id = {}
            if 'id' in new_df.columns:
                for _, row in new_df.iterrows():
                    row_id = row['id']
                    new_data_by_id[row_id] = row
            
            # Обновляем данные из новой таблицы
            for idx in result_df.index:
                row_id = result_df.at[idx, 'id']
                if row_id in new_data_by_id:
                    new_row = new_data_by_id[row_id]
                    
                    # Заполняем все столбцы из новой таблицы
                    for col in new_df.columns:
                        if col in result_df.columns and pd.notna(new_row[col]):
                            # Применяем правило конфликта для имен
                            if col == 'Имя' and conflict_rule != 'A':
                                if conflict_rule == 'B':
                                    # Полностью заменяем на новые имена
                                    result_df.at[idx, col] = new_row[col]
                                elif conflict_rule == 'C':
                                    # Приоритет новым именам
                                    result_df.at[idx, col] = new_row[col]
                            else:
                                # Для остальных столбцов просто заполняем
                                result_df.at[idx, col] = new_row[col]
            
            # Добавляем новые строки из новой таблицы
            existing_ids = set(result_df['id'].tolist())
            new_rows_to_add = []
            
            for _, new_row in new_df.iterrows():
                if new_row['id'] not in existing_ids:
                    new_row_data = {}
                    # Заполняем все столбцы
                    for col in all_columns:
                        if col in new_row and pd.notna(new_row[col]):
                            new_row_data[col] = new_row[col]
                        else:
                            new_row_data[col] = None
                    new_rows_to_add.append(new_row_data)
            
            if new_rows_to_add:
                new_rows_df = pd.DataFrame(new_rows_to_add)
                result_df = pd.concat([result_df, new_rows_df], ignore_index=True)
            
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
            common_cols = len(old_cols & new_cols)
            
            # Анализируем строки
            common_columns = list(old_cols & new_cols)
            if common_columns:
                old_combined = old_df[common_columns].fillna('').astype(str).sum(axis=1)
                new_combined = new_df[common_columns].fillna('').astype(str).sum(axis=1)
                
                old_hashes = set(old_combined)
                new_hashes = set(new_combined)
                
                added_rows = len(new_hashes - old_hashes)
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
