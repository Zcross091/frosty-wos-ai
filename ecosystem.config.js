module.exports = {
  apps: [
    {
      name: 'frosty-discord-bot',
      script: 'bot.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '800M',
      restart_delay: 4000,
      env: {
        PYTHONUNBUFFERED: '1'
      }
    },
    {
      name: 'frosty-api-server',
      script: 'server.py',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '600M',
      restart_delay: 3000,
      env: {
        PORT: '8000',
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};
