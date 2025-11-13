import pandas as pd
import logging
from typing import Dict, Any, Tuple, List, Optional

logger = logging.getLogger(__name__)

class ScenarioApplier:
    """Универсальный применятель сценариев объединения таблиц"""
    
    @staticmethod
    def apply_scenario_1(old_df: pd.DataFrame, new_df: pd.DataFrame, 
                        key_column: Optional[str] = None, conflict_rule: str = 'A') -> Tuple[pd.DataFrame, str]:
        """
        Сценарий 1: Сохранить структуру + добавить строки
        """
        logger.info(f"🔄 Сценарий 1 с ключом: {key_column}")
        
        try:
            result_df = old_df.copy()
            common_columns = list(set(old_df.columns) & set(new_df.columns))
            
            if not common_columns:
                return old_df, "❌ Нет общих столбцов для объединения"
            
            new_rows_df = ScenarioApplier._get_new_rows(old_df, new_df, key_column, common_columns)
            
            if not new_rows_df.empty:
                result_df = pd.concat([result_df, new_rows_df], ignore_index=True)
                
                # Применяем разрешение конфликтов для существующих строк
                if key_column and conflict_rule != 'A':
                    ScenarioApplier._apply_conflict_resolution(result_df, new_df, key_column, conflict_rule)
                
                message = f"✅ Добавлено {len(new_rows_df)} новых строк"
            else:
                message = "✅ Новых строк не найдено"
            
            return result_df, message
            
        except Exception as e:
            logger.error(f"❌ Ошибка в сценарии 1: {e}")
            return old_df, f"❌ Ошибка: {str(e)}"
    
    @staticmethod
    def apply_scenario_2(old_df: pd.DataFrame, new_df: pd.DataFrame, 
                        key_column: Optional[str] = None, conflict_rule: str = 'A') -> Tuple[pd.DataFrame, str]:
        """
        Сценарий 2: Расширить структуру + сохранить строки
        """
        logger.info(f"🔄 Сценарий 2 с ключом: {key_column}")
        
        try:
            result_df = old_df.copy()
            
            # Добавляем новые столбцы
            new_columns = list(set(new_df.columns) - set(old_df.columns))
            for col in new_columns:
                result_df[col] = None
            
            # Заполняем данные из новой таблицы
            if key_column and key_column in old_df.columns and key_column in new_df.columns:
                ScenarioApplier._fill_new_columns(result_df, new_df, key_column, new_columns, conflict_rule)
                message = f"✅ Добавлено {len(new_columns)} столбцов"
            else:
                message = f"✅ Добавлено {len(new_columns)} столбцов (данные не заполнены)"
            
            return result_df, message
            
        except Exception as e:
            logger.error(f"❌ Ошибка в сценарии 2: {e}")
            return old_df, f"❌ Ошибка: {str(e)}"
    
    @staticmethod
    def apply_scenario_3(old_df: pd.DataFrame, new_df: pd.DataFrame, 
                        key_column: Optional[str] = None, conflict_rule: str = 'A') -> Tuple[pd.DataFrame, str]:
        """
        Сценарий 3: Полное объединение
        """
        logger.info(f"🔄 Сценарий 3 с ключом: {key_column}")
        
        try:
            # Создаем полный набор столбцов
            all_columns = list(set(old_df.columns) | set(new_df.columns))
            result_df = pd.DataFrame(columns=all_columns)
            
            # Добавляем данные из старой таблицы
            for col in old_df.columns:
                result_df[col] = old_df[col]
            
            # Добавляем недостающие столбцы
            for col in new_df.columns:
                if col not in result_df.columns:
                    result_df[col] = None
            
            # Обновляем данные из новой таблицы и добавляем новые строки
            if key_column and key_column in new_df.columns:
                result_df = ScenarioApplier._merge_with_key(result_df, new_df, key_column, conflict_rule)
                message = f"✅ Полное объединение: {len(result_df)} строк"
            else:
                # Fallback: просто объединяем таблицы
                result_df = pd.concat([result_df, new_df], ignore_index=True)
                result_df = result_df.drop_duplicates()
                message = f"✅ Объединение: {len(result_df)} строк"
            
            return result_df, message
            
        except Exception as e:
            logger.error(f"❌ Ошибка в сценарии 3: {e}")
            return old_df, f"❌ Ошибка: {str(e)}"
    
    @staticmethod
    def _get_new_rows(old_df: pd.DataFrame, new_df: pd.DataFrame, 
                     key_column: Optional[str], common_columns: List[str]) -> pd.DataFrame:
        """Находит новые строки для добавления"""
        if key_column and key_column in old_df.columns and key_column in new_df.columns:
            # По ключевому столбцу
            old_keys = set(old_df[key_column].dropna().astype(str))
            new_keys = set(new_df[key_column].dropna().astype(str))
            new_row_keys = new_keys - old_keys
            return new_df[new_df[key_column].astype(str).isin(new_row_keys)][common_columns]
        elif key_column == "all_columns":
            # По всем общим столбцам
            old_combined = old_df[common_columns].fillna('').astype(str).sum(axis=1)
            new_combined = new_df[common_columns].fillna('').astype(str).sum(axis=1)
            new_hashes = set(new_combined) - set(old_combined)
            return new_df[new_combined.isin(new_hashes)][common_columns]
        else:
            # Без ключа - добавляем все строки
            return new_df[common_columns]
    
    @staticmethod
    def _apply_conflict_resolution(result_df: pd.DataFrame, new_df: pd.DataFrame, 
                                 key_column: str, conflict_rule: str):
        """Применяет разрешение конфликтов имен"""
        if conflict_rule == 'A':  # Сохранить старые имена
            return
        
        name_mapping = {}
        for _, row in new_df.iterrows():
            if pd.notna(row[key_column]) and 'Имя' in row and pd.notna(row['Имя']):
                name_mapping[str(row[key_column])] = row['Имя']
        
        for idx in result_df.index:
            if pd.notna(result_df.at[idx, key_column]) and 'Имя' in result_df.columns:
                key_val = str(result_df.at[idx, key_column])
                if key_val in name_mapping:
                    result_df.at[idx, 'Имя'] = name_mapping[key_val]
    
    @staticmethod
    def _fill_new_columns(result_df: pd.DataFrame, new_df: pd.DataFrame, 
                         key_column: str, new_columns: List[str], conflict_rule: str):
        """Заполняет новые столбцы данными из новой таблицы"""
        for idx in result_df.index:
            if pd.notna(result_df.at[idx, key_column]):
                key_val = result_df.at[idx, key_column]
                matching_rows = new_df[new_df[key_column] == key_val]
                
                if not matching_rows.empty:
                    match_row = matching_rows.iloc[0]
                    for col in new_columns:
                        if col in match_row and pd.notna(match_row[col]):
                            result_df.at[idx, col] = match_row[col]
                    
                    # Применяем конфликт имен
                    if conflict_rule != 'A' and 'Имя' in result_df.columns and 'Имя' in match_row:
                        if pd.notna(match_row['Имя']):
                            result_df.at[idx, 'Имя'] = match_row['Имя']
    
    @staticmethod
    def _merge_with_key(result_df: pd.DataFrame, new_df: pd.DataFrame, 
                       key_column: str, conflict_rule: str) -> pd.DataFrame:
        """Объединяет таблицы по ключевому столбцу"""
        # Обновляем существующие строки
        for idx in result_df.index:
            if pd.notna(result_df.at[idx, key_column]):
                key_val = result_df.at[idx, key_column]
                matching_rows = new_df[new_df[key_column] == key_val]
                
                if not matching_rows.empty:
                    match_row = matching_rows.iloc[0]
                    for col in new_df.columns:
                        if col in result_df.columns and pd.notna(match_row[col]):
                            if col == 'Имя' and conflict_rule != 'A':
                                result_df.at[idx, col] = match_row[col]
                            else:
                                result_df.at[idx, col] = match_row[col]
        
        # Добавляем новые строки
        existing_keys = set(result_df[key_column].dropna())
        new_keys = set(new_df[key_column].dropna())
        new_row_keys = new_keys - existing_keys
        
        if new_row_keys:
            new_rows = new_df[new_df[key_column].isin(new_row_keys)]
            result_df = pd.concat([result_df, new_rows], ignore_index=True)
        
        return result_df
    
    @staticmethod
    def apply_scenario(scenario: str, old_df: pd.DataFrame, new_df: pd.DataFrame, 
                      key_column: Optional[str] = None, conflict_rule: str = 'A') -> Tuple[pd.DataFrame, str]:
        """Применяет выбранный сценарий"""
        scenarios = {
            '1': ScenarioApplier.apply_scenario_1,
            '2': ScenarioApplier.apply_scenario_2,
            '3': ScenarioApplier.apply_scenario_3,
        }
        
        if scenario in scenarios:
            return scenarios[scenario](old_df, new_df, key_column, conflict_rule)
        else:
            logger.error(f"❌ Неизвестный сценарий: {scenario}")
            return old_df, f"❌ Неизвестный сценарий: {scenario}"
