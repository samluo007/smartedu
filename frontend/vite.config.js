import { defineConfig, loadEnv } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd())

  return {
    plugins: [
      vue(),
    ],

    // ==================== 路径别名 ====================
    resolve: {
      alias: {
        '@': resolve(__dirname, 'src'),
        '@components': resolve(__dirname, 'src/components'),
        '@views': resolve(__dirname, 'src/views'),
        '@assets': resolve(__dirname, 'src/assets'),
        '@api': resolve(__dirname, 'src/api'),
        '@utils': resolve(__dirname, 'src/utils'),
        '@store': resolve(__dirname, 'src/store'),
      },
      // 优化依赖解析性能
      dedupe: ['vue', 'vue-router', 'element-plus'],
    },

    // ==================== CSS 配置 ====================
    css: {
      preprocessorOptions: {
        scss: {
          // 全局 SCSS 变量（如有需要）
          additionalData: '',
        },
      },
      // 开发环境启用 source map，生产关闭
      devSourcemap: mode === 'development',
    },

    // ==================== 构建优化（生产环境） ====================
    build: {
      // 输出目录
      outDir: 'dist',
      // 静态资源目录
      assetsDir: 'assets',
      // 小于此阈值的资源内联为 base64（减少请求数）
      assetsInlineLimit: 4096,
      // 启用 CSS code splitting
      cssCodeSplit: true,
      // 构建时生成 source map
      sourcemap: false,

      // chunk 分割策略 —— 核心优化点
      rollupOptions: {
        output: {
          // 分组命名规则
          manualChunks: {
            // Vue 核心 + 路由（稳定不变，长期缓存）
            'vue-vendor': ['vue', 'vue-router', 'pinia'],
            // Element Plus UI 库（最大依赖）
            'element-plus': ['element-plus', '@element-plus/icons-vue'],
            // 工具库（lodash/dayjs 等中体积依赖）
            'utils': [],
          },
          // chunk 文件命名（带 content hash 实现长效缓存）
          chunkFileNames: 'static/js/[name].[hash:8].js',
          entryFileNames: 'static/js/[name].[hash:8].js',
          assetFileNames: (assetInfo) => {
            const ext = assetInfo.name?.split('.').pop() || ''
            if (/\.(png|jpe?g|gif|svg|webp|ico)$/i.test(ext)) {
              return `static/images/[name].[hash:8][extname]`
            }
            if (/\.(woff2?|eot|ttf|otf)$/i.test(ext)) {
              return `static/fonts/[name].[hash:8][extname]`
            }
            if (/\.css$/i.test(ext)) {
              return `static/css/[name].[hash:8][extname]`
            }
            return `static/assets/[name].[hash:8][extname]`
          },
        },
      },

      // 压缩配置
      minify: 'terser',
      terserOptions: {
        compress: {
          drop_console: true,       // 生产移除 console
          drop_debugger: true,      // 移除 debugger
          pure_funcs: [
            'console.log',
            'console.info',
            'console.debug',
          ],
        },
        output: {
          comments: false,         // 移除注释
          beautify: false,
        },
      },

      // chunk 大小警告阈值
      chunkSizeWarningLimit: 500,
    },

    // ==================== 开发服务器配置 ====================
    server: {
      port: parseInt(env.VITE_APP_PORT || '5173'),
      host: '0.0.0.0',
      open: true,                  // 自动打开浏览器

      // API 代理（开发环境转发到后端 Flask）
      proxy: {
        '/api': {
          target: env.VITE_API_URL || 'http://localhost:5000',
          changeOrigin: true,
          rewrite: (path) => path,
          // 代理错误日志
          configure: (proxy, options) => {
            proxy.on('error', (err, req, res) => {
              console.log('[Proxy Error]', err.message)
            })
            proxy.on('proxyRes', (proxyReq, req, res) => {
              if (req.path.includes('/api/')) {
                console.log(`[API Proxy] ${req.method} ${req.path} → ${proxyReq.statusCode}`)
              }
            })
          }
        }
      },

      // 预热文件（减少首屏冷启动时间）
      warmup: {
        clientFiles: ['./src/main.ts', './src/App.vue']
      }
    },

    // ==================== 预览配置 ====================
    preview: {
      port: 4173,
      host: '0.0.0.0',
    },

    // ==================== 性能优化选项 ====================
    optimizeDeps: {
      include: [
        'vue',
        'vue-router',
        'element-plus',
        '@element-plus/icons-vue',
        'axios',
      ],
      // 强制预构建（解决某些包的 CJS/ESM 问题）
    },

    // ES 目标版本
    esbuild: {
      target: 'es2020',
      // 生产环境移除 lodash 等库的副作用
      drop: mode === 'production' ? ['debugger'] : [],
    },
  }
})
