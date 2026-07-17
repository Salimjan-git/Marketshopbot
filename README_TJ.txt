ҚАДАМИ МУҲИМ

Сохтори brands иваз шуд: ҳар бренд category_id дорад.

Азбаски SQLite CREATE TABLE IF NOT EXISTS таблицаи кӯҳнаро тағйир намедиҳад,
дар development базаи кӯҳнаро backup гиред ва аз нав созед:

cp my_database my_database_backup
rm -f my_database
python3 database.py

Агар DB_NAME-и шумо marketplace.db бошад, ҳамон номро истифода баред.

Файлҳоро ҷойгир кунед:
database.py -> project/database.py
admin.py -> project/handlers/admin.py
admin_manage.py -> project/handlers/admin_manage.py
catalog.py -> project/handlers/catalog.py
admin_keyboard.py -> project/keyboards/admin.py

Баъд:
find . -type d -name "__pycache__" -exec rm -rf {} +
python3 app.py