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
                # Используем все общие столбцы для сравнения
                old_combined = old_df[common_columns].astype(str).sum(axis=1)
                new_combined = new_df[common_columns].astype(str).sum(axis=1)
                
                old_hashes = set(old_combined)
                new_hashes = set(new_combined)
                
                new_rows_hashes = new_hashes - old_hashes
                new_rows_mask = new_combined.isin(new_rows_hashes)
                
                if new_rows_mask.any():
                    # Берем только общие столбцы из новых строк
                    new_rows_df = new_df.loc[new_rows_mask, common_columns]
                    
                    # Применяем правило конфликта для имен
                    if 'Имя' in common_columns and conflict_rule != 'A':
                        # Для правила B и C используем имена из новой таблицы
                        if conflict_rule == 'B':
                            # Полностью заменяем имена на новые
                            pass  # Уже берем из новой таблицы
                        elif conflict_rule == 'C':
                            # Приоритет новым именам, но сохраняем старые если новых нет
                            # В данном случае просто берем новые имена
                            pass  # Уже берем из новой таблицы
                    
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
            
            # Заполняем новые столбцы данными из новой таблицы для существующих строк
            # Используем merge для сопоставления по общим столбцам
            common_columns = list(set(old_df.columns) & set(new_df.columns))
            
            if common_columns:
                # Объединяем старую таблицу с новой по общим столбцам
                merged = pd.merge(result_df, new_df, on=common_columns, how='left', suffixes=('', '_new'))
                
                # Заполняем новые столбцы данными из объединенной таблицы
                for col in new_columns:
                    if f"{col}_new" in merged.columns:
                        result_df[col] = merged[f"{col}_new"]
                    elif col in merged.columns:
                        result_df[col] = merged[col]
                
                # Применяем правило конфликта для имен
                if 'Имя' in common_columns and conflict_rule != 'A':
                    if conflict_rule in ['B', 'C']:
                        # Берем имена из новой таблицы
                        for idx in result_df.index:
                            # Находим соответствующую строку в новой таблице
                            match_mask = True
                            for common_col in common_columns:
                                if common_col != 'Имя':
                                    old_val = result_df.at[idx, common_col]
                                    # Ищем совпадение в новой таблице
                                    new_match = new_df[new_df[common_col] == old_val]
                                    if not new_match.empty and 'Имя' in new_match.columns:
                                        result_df.at[idx, 'Имя'] = new_match.iloc[0]['Имя']
                                        break
            
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
            # Начинаем со старой таблицы
            result_df = old_df.copy()
            
            # Добавляем новые столбцы из новой таблицы
            new_columns = list(set(new_df.columns) - set(old_df.columns))
            for col in new_columns:
                result_df[col] = None
            
            # Определяем общие столбцы
            common_columns = list(set(old_df.columns) & set(new_df.columns))
            
            # Добавляем новые строки из новой таблицы
            if common_columns:
                # Находим строки в новой таблице, которых нет в старой
                old_combined = old_df[common_columns].astype(str).sum(axis=1)
                new_combined = new_df[common_columns].astype(str).sum(axis=1)
                
                old_hashes = set(old_combined)
                new_hashes = set(new_combined)
                
                new_rows_hashes = new_hashes - old_hashes
                new_rows_mask = new_combined.isin(new_rows_hashes)
                
                if new_rows_mask.any():
                    new_rows_df = new_df.loc[new_rows_mask]
                    
                    # Для новых строк добавляем недостающие столбцы
                    for col in old_df.columns:
                        if col not in new_rows_df.columns:
                            new_rows_df[col] = None
                    
                    result_df = pd.concat([result_df, new_rows_df], ignore_index=True)
            
            # Заполняем данные из новой таблицы для всех строк
            if common_columns:
                # Создаем временный объединенный DataFrame
                temp_merged = pd.merge(result_df, new_df, on=common_columns, how='left', suffixes=('', '_new'))
                
                # Заполняем новые столбцы данными из новой таблицы
                for col in new_columns:
                    if f"{col}_new" in temp_merged.columns:
                        result_df[col] = temp_merged[f"{col}_new"]
                    elif col in temp_merged.columns:
                        result_df[col] = temp_merged[col]
                
                # Применяем правило конфликта для имен
                if 'Имя' in common_columns and conflict_rule != 'A':
                    if conflict_rule in ['B', 'C']:
                        # Создаем маппинг из новой таблицы
                        name_mapping = {}
                        for idx, row in new_df.iterrows():
                            key = tuple(str(row[col]) for col in common_columns if col != 'Имя')
                            if key and 'Имя' in row:
                                name_mapping[key] = row['Имя']
                        
                        # Обновляем имена в result_df
                        for idx in result_df.index:
                            key = tuple(str(result_df.at[idx, col]) for col in common_columns if col != 'Имя')
                            if key in name_mapping:
                                result_df.at[idx, 'Имя'] = name_mapping[key]
            
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
                old_combined = old_df[common_columns].astype(str).sum(axis=1)
                new_combined = new_df[common_columns].astype(str).sum(axis=1)
                
                old_hashes = set(old_combined)
                new_hashes = set(new_combined)
                
                added_rows = len(new_hashes - old_hashes)
            else:
                added_rows = len(new_df)
            
            # Эвристика для выбора сценария
            if added_cols > 2 and added_rows > 2:
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
