module.exports = {
  apps: [
    {
      name: 'frosty-wos-ai',
      script: 'bot.py',
      // If using python virtual environment on Linux/Oracle cloud:
      // interpreter: './.venv/bin/python3',
      interpreter: 'python3',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '800M',
      restart_delay: 4000,
      max_restarts: 10,
      env: {
        NODE_ENV: 'production',
        PYTHONUNBUFFERED: '1'
      }
    }
  ]
};
