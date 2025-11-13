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
        """
        logger.info("🔄 Применение сценария 1: Сохранить структуру + добавить строки")
        
        try:
            # Сохраняем оригинальные столбцы старой таблицы
            result_df = old_df.copy()
            
            # Добавляем новые строки из новой таблицы (только по общим столбцам)
            common_columns = list(set(old_df.columns) & set(new_df.columns))
            
            if common_columns:
                # Находим новые строки (которые отсутствуют в старой таблице)
                old_hashes = set(old_df.astype(str).sum(axis=1).apply(hash))
                new_hashes = set(new_df.astype(str).sum(axis=1).apply(hash))
                
                new_rows_hashes = new_hashes - old_hashes
                new_rows_mask = new_df.astype(str).sum(axis=1).apply(hash).isin(new_rows_hashes)
                
                if new_rows_mask.any():
                    new_rows_df = new_df.loc[new_rows_mask, common_columns]
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
        """
        logger.info("🔄 Применение сценария 2: Расширить структуру + сохранить строки")
        
        try:
            result_df = old_df.copy()
            
            # Добавляем новые столбцы из новой таблицы
            new_columns = list(set(new_df.columns) - set(old_df.columns))
            
            for col in new_columns:
                result_df[col] = None  # Заполняем новыe столбцы пустыми значениями
            
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
        """
        logger.info("🔄 Применение сценария 3: Полное объединение")
        
        try:
            # Объединяем столбцы
            all_columns = list(set(old_df.columns) | set(new_df.columns))
            
            # Создаем DataFrame с всеми столбцами
            result_df = pd.DataFrame(columns=all_columns)
            
            # Добавляем данные из старой таблицы
            for col in old_df.columns:
                result_df[col] = old_df[col]
            
            # Добавляем данные из новой таблицы
            for col in new_df.columns:
                if col in result_df.columns:
                    # Если столбец уже есть, объединяем данные
                    mask = result_df[col].isna()
                    result_df.loc[mask, col] = new_df[col]
                else:
                    result_df[col] = new_df[col]
            
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
        """
        logger.info("🔄 Применение сценария 4: Умное объединение")
        
        try:
            # Анализируем, какой сценарий лучше
            old_cols = set(old_df.columns)
            new_cols = set(new_df.columns)
            
            added_cols = len(new_cols - old_cols)
            common_cols = len(old_cols & new_cols)
            
            # Эвристика для выбора сценария
            if added_cols > 0 and common_cols > 0:
                # Если есть новые столбцы и общие - полное объединение
                result_df, message = ScenarioApplier.apply_scenario_3(old_df, new_df, conflict_rule)
                message = f"⚡ Умное объединение: {message}"
            elif added_cols > 0:
                # Если только новые столбцы - расширяем структуру
                result_df, message = ScenarioApplier.apply_scenario_2(old_df, new_df, conflict_rule)
                message = f"⚡ Умное объединение: {message}"
            else:
                # Иначе - добавляем строки
                result_df, message = ScenarioApplier.apply_scenario_1(old_df, new_df, conflict_rule)
                message = f"⚡ Умное объединение: {message}"
            
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
