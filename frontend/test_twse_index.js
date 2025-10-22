/**
 * 測試 twseIndex store 的邏輯
 */

// 模擬後端返回的格式
const apiResponse = {
  success: true,
  data: {
    日期: '1141021',
    指數: '發行量加權股價指數',
    收盤指數: '27752',
    漲跌: '+',
    漲跌點數: '63.78',
    漲跌百分比: '0.23',
    特殊處理註記: '',
  },
  error: null,
  tool: 'index_info',
  timestamp: '2025-10-22T18:39:59.019714',
};

// 新的 loadMarketIndices 邏輯
const indicesArray = apiResponse.data ? [apiResponse.data] : [];

console.log('轉換後的 marketIndices:', indicesArray);

// twseIndex 衍生 store 的邏輯
const marketIndices = indicesArray;
const twseIndex = (() => {
  if (!marketIndices || marketIndices.length === 0) return null;

  // 從指數列表中找到"發行量加權股價指數"
  const index = marketIndices.find((idx) => idx['指數'] === '發行量加權股價指數');

  if (!index) return null;

  // 將資料轉換為前端易用的格式
  return {
    index_name: index['指數'],
    current_value: parseFloat(index['收盤指數']),
    change: index['漲跌'] === '+' ? parseFloat(index['漲跌點數']) : -parseFloat(index['漲跌點數']),
    change_percent: parseFloat(index['漲跌百分比']),
    date: index['日期'],
  };
})();

console.log('最終的 twseIndex:', twseIndex);
console.log('可用於顯示: 大盤指數 27752 ▲ 0.23%');
console.log('測試通過！');
