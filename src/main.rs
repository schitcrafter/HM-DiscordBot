use tracing::{error, info};

mod bot;
mod mysql_lib;
mod redis_lib;

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let redis = redis_lib::get_connection().await.unwrap();
    info!("Successfully connected to redis");

    let sql_pool = mysql_lib::get_connection(5).await.unwrap();
    info!("Successfully connected to MySQL Database");

    if let Err(err) = mysql_lib::migrate_database(&sql_pool).await {
        error!(error = err.to_string(), "SQL Migration failed");
        return;
    }
    info!("Successfully made the SQL migration if any");

    bot::entrypoint(sql_pool, redis).await;
}
