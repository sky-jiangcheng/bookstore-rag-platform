// 检查Element Plus Icons中可用的图标
import * as ElIcons from '@element-plus/icons-vue';

// 打印所有图标名称
console.log('Element Plus Icons available:');
console.log(Object.keys(ElIcons));

// 检查是否有Send相关的图标
const sendIcons = Object.keys(ElIcons).filter(key => 
  key.toLowerCase().includes('send') || 
  key.toLowerCase().includes('message') ||
  key.toLowerCase().includes('chat')
);

console.log('\nSend-related icons:');
console.log(sendIcons);
