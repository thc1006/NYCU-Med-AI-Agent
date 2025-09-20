/**
 * 健康資源元件 - 現代化玻璃擬態設計
 */

import React, { useState } from 'react';
import {
  Heart, Shield, Activity, Brain, Apple, Moon,
  Users, BookOpen, Video, Download, ExternalLink,
  Calendar, Award, Star,
  Clock, Target, Zap, Info
} from 'lucide-react';

interface ResourceCategory {
  id: string;
  title: string;
  icon: React.ComponentType<any>;
  color: string;
  description: string;
  resources: Resource[];
}

interface Resource {
  title: string;
  description: string;
  link?: string;
  tags: string[];
  rating?: number;
  downloads?: number;
}

const HealthResources: React.FC = () => {
  const [activeCategory, setActiveCategory] = useState<string>('prevention');

  const categories: ResourceCategory[] = [
    {
      id: 'prevention',
      title: '預防保健',
      icon: Shield,
      color: 'blue',
      description: '疾病預防與健康促進資源',
      resources: [
        {
          title: '成人預防保健手冊',
          description: '40歲以上成人健康檢查指南，包含各項篩檢項目說明',
          link: 'https://www.hpa.gov.tw',
          tags: ['健檢', '預防', '指南'],
          rating: 4.8,
          downloads: 15420
        },
        {
          title: '四癌篩檢懶人包',
          description: '大腸癌、口腔癌、乳癌、子宮頸癌篩檢完整說明',
          link: 'https://www.hpa.gov.tw',
          tags: ['癌症', '篩檢', '免費'],
          rating: 4.9,
          downloads: 23150
        },
        {
          title: '疫苗接種時程表',
          description: '各年齡層建議接種疫苗時程與注意事項',
          tags: ['疫苗', '兒童', '成人'],
          rating: 4.7,
          downloads: 18930
        }
      ]
    },
    {
      id: 'nutrition',
      title: '營養飲食',
      icon: Apple,
      color: 'green',
      description: '健康飲食指南與營養建議',
      resources: [
        {
          title: '國民飲食指南',
          description: '每日飲食建議與六大類食物攝取指引',
          link: 'https://www.hpa.gov.tw',
          tags: ['營養', '飲食', '指南'],
          rating: 4.6,
          downloads: 28470
        },
        {
          title: '糖尿病飲食控制',
          description: '血糖管理與食物代換技巧完整教學',
          tags: ['糖尿病', '血糖', '飲食'],
          rating: 4.8,
          downloads: 19820
        },
        {
          title: '高血壓DASH飲食',
          description: '降血壓飲食計畫與食譜分享',
          tags: ['高血壓', 'DASH', '食譜'],
          rating: 4.7
        }
      ]
    },
    {
      id: 'exercise',
      title: '運動健身',
      icon: Activity,
      color: 'orange',
      description: '運動處方與體適能指導',
      resources: [
        {
          title: '333運動處方',
          description: '每週3次、每次30分鐘、心跳130的運動建議',
          tags: ['運動', '有氧', '處方'],
          rating: 4.5,
          downloads: 12380
        },
        {
          title: '銀髮族運動指南',
          description: '適合65歲以上長者的安全運動方案',
          tags: ['銀髮', '長者', '安全'],
          rating: 4.9,
          downloads: 16290
        },
        {
          title: '居家徒手訓練',
          description: '不需器材的全身肌力訓練動作教學',
          tags: ['居家', '肌力', '徒手'],
          rating: 4.7
        }
      ]
    },
    {
      id: 'mental',
      title: '心理健康',
      icon: Brain,
      color: 'purple',
      description: '壓力管理與心理支持資源',
      resources: [
        {
          title: '壓力自我評估量表',
          description: '評估個人壓力程度與因應建議',
          tags: ['壓力', '評估', '自我檢測'],
          rating: 4.6,
          downloads: 21560
        },
        {
          title: '正念減壓課程',
          description: '8週正念練習計畫與引導音頻',
          tags: ['正念', '冥想', '減壓'],
          rating: 4.8,
          downloads: 17840
        },
        {
          title: '憂鬱症認識與陪伴',
          description: '認識憂鬱症狀與陪伴者指引',
          tags: ['憂鬱', '心理', '陪伴'],
          rating: 4.9
        }
      ]
    },
    {
      id: 'sleep',
      title: '睡眠衛生',
      icon: Moon,
      color: 'indigo',
      description: '改善睡眠品質的方法與建議',
      resources: [
        {
          title: '睡眠衛生十大守則',
          description: '建立良好睡眠習慣的實用建議',
          tags: ['睡眠', '失眠', '習慣'],
          rating: 4.7,
          downloads: 14920
        },
        {
          title: '睡眠日誌範本',
          description: '記錄睡眠狀況找出問題根源',
          tags: ['日誌', '記錄', '分析'],
          rating: 4.5
        }
      ]
    },
    {
      id: 'community',
      title: '社區資源',
      icon: Users,
      color: 'teal',
      description: '在地健康服務與支持團體',
      resources: [
        {
          title: '社區關懷據點',
          description: '全台社區照顧關懷據點查詢',
          link: 'https://ccare.sfaa.gov.tw',
          tags: ['社區', '長照', '據點'],
          rating: 4.6
        },
        {
          title: '病友支持團體',
          description: '各類疾病病友會與支持團體資訊',
          tags: ['病友', '支持', '團體'],
          rating: 4.8
        }
      ]
    }
  ];

  const currentCategory = categories.find(cat => cat.id === activeCategory) || categories[0];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* 標題區塊 */}
      <div className="text-center space-y-3">
        <h2 className="text-3xl font-bold text-gray-800 flex items-center justify-center">
          <Heart className="w-8 h-8 text-red-500 mr-3 animate-pulse" />
          健康資源中心
        </h2>
        <p className="text-gray-600 max-w-2xl mx-auto">
          提供您最完整的健康促進資源，從預防保健到疾病管理，協助您掌握自己的健康
        </p>
      </div>

      {/* 分類選擇器 - 橫向滾動 */}
      <div className="overflow-x-auto pb-2">
        <div className="flex space-x-3 min-w-max">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => setActiveCategory(category.id)}
              className={`
                group relative px-6 py-4 rounded-2xl
                transform transition-all duration-300
                ${activeCategory === category.id
                  ? 'bg-gradient-brand text-white shadow-glow scale-105'
                  : 'glass-card hover:scale-102 hover:shadow-card'
                }
              `}
            >
              <div className="flex items-center space-x-3">
                <category.icon className={`w-5 h-5 ${
                  activeCategory === category.id ? 'text-white' : 'text-brand-600'
                }`} />
                <div className="text-left">
                  <div className={`font-semibold ${
                    activeCategory === category.id ? 'text-white' : 'text-gray-800'
                  }`}>
                    {category.title}
                  </div>
                  <div className={`text-xs ${
                    activeCategory === category.id ? 'text-white/80' : 'text-gray-500'
                  }`}>
                    {category.resources.length} 項資源
                  </div>
                </div>
              </div>

              {/* 選中指示器 */}
              {activeCategory === category.id && (
                <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-8 h-1 bg-white rounded-full animate-pulse" />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* 分類描述 */}
      <div className="glass-card rounded-2xl p-6 bg-gradient-to-r from-brand-50/50 to-medical-50/50">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-white/70 rounded-xl backdrop-blur-sm">
            <currentCategory.icon className="w-6 h-6 text-brand-600" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-gray-800">{currentCategory.title}</h3>
            <p className="text-gray-600">{currentCategory.description}</p>
          </div>
        </div>
      </div>

      {/* 資源卡片網格 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {currentCategory.resources.map((resource, index) => (
          <div
            key={index}
            className={`
              group relative glass-card rounded-2xl p-6
              transform transition-all duration-500
              hover:scale-102 hover:shadow-float
              opacity-0 animate-fade-in
            `}
            style={{ animationDelay: `${index * 100}ms`, opacity: 1 }}
          >
            {/* 評分標記 */}
            {resource.rating && (
              <div className="absolute top-4 right-4 flex items-center space-x-1
                            bg-yellow-50/80 backdrop-blur-sm rounded-lg px-2 py-1">
                <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                <span className="text-sm font-semibold text-yellow-700">
                  {resource.rating}
                </span>
              </div>
            )}

            {/* 標題 */}
            <h4 className="text-lg font-bold text-gray-800 mb-3 pr-12">
              {resource.title}
            </h4>

            {/* 描述 */}
            <p className="text-sm text-gray-600 mb-4 line-clamp-2">
              {resource.description}
            </p>

            {/* 標籤 */}
            <div className="flex flex-wrap gap-2 mb-4">
              {resource.tags.map((tag, tagIndex) => (
                <span
                  key={tagIndex}
                  className="px-3 py-1 bg-brand-50/50 text-brand-700
                           text-xs font-medium rounded-full backdrop-blur-sm"
                >
                  #{tag}
                </span>
              ))}
            </div>

            {/* 統計資訊 */}
            {resource.downloads && (
              <div className="flex items-center justify-between text-xs text-gray-500
                            pt-4 border-t border-gray-100">
                <div className="flex items-center space-x-1">
                  <Download className="w-3 h-3" />
                  <span>{resource.downloads.toLocaleString()} 次下載</span>
                </div>
                {resource.link && (
                  <a
                    href={resource.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center space-x-1 text-brand-600
                             hover:text-brand-700 transition-colors"
                  >
                    <span>查看更多</span>
                    <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            )}

            {/* Hover 效果光暈 */}
            <div className={`
              absolute inset-0 rounded-2xl pointer-events-none
              bg-gradient-to-br from-brand-400/10 to-transparent
              opacity-0 group-hover:opacity-100 transition-opacity duration-500
            `} />
          </div>
        ))}
      </div>

      {/* 快速連結區塊 */}
      <div className="glass-card rounded-3xl p-8 bg-gradient-to-br from-medical-50/30 to-brand-50/30">
        <h3 className="text-2xl font-bold text-gray-800 mb-6 flex items-center">
          <Zap className="w-7 h-7 text-yellow-500 mr-3" />
          快速連結
        </h3>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { icon: Calendar, label: '預約掛號', color: 'blue' },
            { icon: BookOpen, label: '衛教手冊', color: 'green' },
            { icon: Video, label: '影音教學', color: 'purple' },
            { icon: Award, label: '健康認證', color: 'orange' }
          ].map((item, index) => (
            <button
              key={index}
              className="group flex flex-col items-center justify-center p-6
                       glass-card rounded-xl hover:shadow-card
                       transform transition-all duration-300 hover:scale-105"
            >
              <div className={`p-3 rounded-full bg-${item.color}-100 mb-3
                            group-hover:bg-${item.color}-200 transition-colors`}>
                <item.icon className={`w-6 h-6 text-${item.color}-600`} />
              </div>
              <span className="text-sm font-medium text-gray-700">
                {item.label}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* 健康小提醒 */}
      <div className="glass-card rounded-2xl p-6 bg-gradient-to-r from-green-50/50 to-blue-50/50">
        <div className="flex items-start space-x-4">
          <div className="p-3 bg-green-100 rounded-xl">
            <Info className="w-6 h-6 text-green-600" />
          </div>
          <div className="flex-1">
            <h4 className="font-bold text-gray-800 mb-2">今日健康提醒</h4>
            <p className="text-sm text-gray-600 mb-3">
              記得每小時起身活動5分鐘，保持良好的工作姿勢，適時補充水分。
              健康的生活習慣從小細節開始！
            </p>
            <div className="flex items-center space-x-4 text-xs text-gray-500">
              <div className="flex items-center space-x-1">
                <Clock className="w-4 h-4" />
                <span>每日更新</span>
              </div>
              <div className="flex items-center space-x-1">
                <Target className="w-4 h-4" />
                <span>個人化建議</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HealthResources;