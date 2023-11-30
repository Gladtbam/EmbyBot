using Microsoft.EntityFrameworkCore;
using Pomelo.EntityFrameworkCore.MySql.Infrastructure;
using LoadConfig;
using Logging;
using System;
using System.Diagnostics.CodeAnalysis;

namespace DataBase
{
    public class User
    {
        public string TelegramId { get; set; }
        public string EmbyId { get; set; }
        public string EmbyName { get; set; }
        public DateTime? LimitDate { get; set; }
        public bool Ban { get; set; }
        public DateTime? DeleteDate { get; set; }
    }
    public class Code
    {
        public string CodeId { get; set; }
        public string TimeStamp { get; set; }
    }
    public class Score
    {
        public string TelegramId { get; set; }
        public int Value { get; set; }
        public int Checkin { get; set; }
        public int Warning { get; set; }
        public DateTime? LastCheckin { get; set; }
    }

    public class DataBaseContext : DbContext
    {
        readonly AppConfig config = Configure.LoadConfigure();
        public DbSet<User> Users { get; set; }
        public DbSet<Code> Codes { get; set; }
        public DbSet<Score> Scores { get; set; }

        protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
        {
            if (!optionsBuilder.IsConfigured)
            {
                optionsBuilder.UseMySql($"Server={config.DataBase.Host},{config.DataBase.Port};Database={config.DataBase.Name};User Id={config.DataBase.User};Password={config.DataBase.Password};", new MySqlServerVersion(new Version(8, 0, 30)));           
            }
        }
        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            modelBuilder.Entity<User>(entity =>
            {
                entity.HasKey(e => e.TelegramId);
                entity.Property(e => e.TelegramId).HasMaxLength(50);
                entity.Property(e => e.EmbyId).HasMaxLength(50);
                entity.Property(e => e.EmbyName).HasMaxLength(50);
                entity.Property(e => e.LimitDate).HasColumnType("datetime");
                entity.Property(e => e.DeleteDate).HasColumnType("datetime");
            });
            modelBuilder.Entity<Code>(entity =>
            {
                entity.HasKey(e => e.CodeId);
                entity.Property(e => e.CodeId).HasMaxLength(50);
                entity.Property(e => e.TimeStamp).HasMaxLength(50);
            });
            modelBuilder.Entity<Score>(entity =>
            {
                entity.HasKey(e => e.TelegramId);
                entity.Property(e => e.TelegramId).HasMaxLength(50);
                entity.Property(e => e.Value).HasMaxLength(50);
                entity.Property(e => e.Checkin).HasMaxLength(50);
                entity.Property(e => e.LastCheckin).HasColumnType("datetime");
            });
        }
        public async Task<bool> CreateUser(string TelegramId, string EmbyId, string EmbyName, bool Ban=false, DateTime? DeleteDate=null)
        {
            DateTime LimitDate = DateTime.Now.AddMonths(1);
            var user = new User
            {
                TelegramId = TelegramId,
                EmbyId = EmbyId,
                EmbyName = EmbyName,
                LimitDate = LimitDate,
                Ban = Ban,
                DeleteDate = DeleteDate
            };
            try
            {
                Users.Add(user);
                await SaveChangesAsync();
                await DisposeAsync();
                return true;
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return false;
            }
        }
        public async Task<bool> DeleteUser(string TelegramId)
        {
            try
            {
                var user = await Users.FindAsync(TelegramId);
                if (user != null)
                {
                    Users.Remove(user);
                    await SaveChangesAsync();
                    await DisposeAsync();
                    return true;
                }
                else
                {
                    return false;
                }
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return false;
            }
        }
        public async Task<User?> SearchUser(string TelegramId)
        {
            try
            {
                var user = await Users.FindAsync(TelegramId);
                await DisposeAsync();
                if (user != null)
                {
                    return user;
                }
                else
                {
                    return null;
                }
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return null;
            }
        }
        public async Task<List<string>?> BanLimitUser()
        {
            try
            {
                var users = await Users.Where(user => user.LimitDate <= DateTime.Now && user.Ban == false).ToListAsync();
                List<string> embyIds = new List<string>();
                foreach (var user in users)
                {
                    user.Ban = true;
                    user.DeleteDate = DateTime.Now.AddDays(7);
                    embyIds.Add(user.EmbyId);
                }
                await SaveChangesAsync();
                await DisposeAsync();
                return embyIds;
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return null;
            }
        }
        public async Task<List<string>?> DeleteBanUser()
        {
            try
            {
                var users = await Users.Where(user => user.DeleteDate <= DateTime.Now && user.Ban == true).ToListAsync();
                List<string> embyIds = new List<string>();
                foreach (var user in users)
                {
                    Users.Remove(user);
                    embyIds.Add(user.EmbyId);
                }
                await SaveChangesAsync();
                await DisposeAsync();
                return embyIds;
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return null;
            }
        }
        public async void UpdateLimitUser(string TelegramId, int days=0)
        {
            try
            {
                var user = await Users.FindAsync(TelegramId);
                if (user != null)
                {
                    if (user.Ban == true)
                        user.Ban = false;
                    if (days == 0)
                        user.LimitDate = DateTime.Now.AddDays(days);
                    else
                        user.LimitDate = DateTime.Now.AddMonths(1);
                    await SaveChangesAsync();
                    await DisposeAsync();
                }
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
            }
        }
        public async Task<bool> CreateScoreUser(string TelegramId, int Value, int Checkin=0, int Warning=0)
        {
            var score = new Score
            {
                TelegramId = TelegramId,
                Value = Value,
                Checkin = Checkin,
                Warning = Warning,
                LastCheckin = DateTime.Now.AddDays(-1).Date.ToString("yyyy-MM-dd") == DateTime.Now.Date.ToString("yyyy-MM-dd") ? DateTime.Now.AddDays(-1) : DateTime.Now.AddDays(-1).Date
            };
            try
            {
                Scores.Add(score);
                await SaveChangesAsync();
                await DisposeAsync();
                return true;
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return false;
            }
        }
        public async Task<bool> DeleteScoreUser(string TelegramId)
        {
            try
            {
                var score = await Scores.FindAsync(TelegramId);
                if (score != null)
                {
                    Scores.Remove(score);
                    await SaveChangesAsync();
                    await DisposeAsync();
                    return true;
                }
                else
                {
                    return false;
                }
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return false;
            }
        }
        public async Task<Score?> SearchScoreUser(string TelegramId)
        {
            try
            {
                var score = await Scores.FindAsync(TelegramId);
                await DisposeAsync();
                if (score != null)
                {
                    return score;
                }
                else
                {
                    return null;
                }
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return null;
            }
        }
        public async Task<bool> ChangeUserScore(string TelegramId, int Value)
        {
            try
            {
                var score = await Scores.FindAsync(TelegramId);
                if (score != null)
                {
                    score.Value += Value;
                    await SaveChangesAsync();
                    await DisposeAsync();
                    return true;
                }
                else
                {
                    return false;
                }
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return false;
            }
        }
        public async Task<bool> ChangeUserCheckin(string TelegramId, int Checkin, DateTime? LastCheckin)
        {
            try
            {
                var score = await Scores.FindAsync(TelegramId);
                if (score != null)
                {
                    score.Checkin += Checkin;
                    score.LastCheckin = DateTime.Now.Date.ToString("yyyy-MM-dd") == LastCheckin?.Date.ToString("yyyy-MM-dd") ? LastCheckin : DateTime.Now.Date;
                    await SaveChangesAsync();
                    await DisposeAsync();
                    return true;
                }
                else
                {
                    return false;
                }
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return false;
            }
        }
        public async Task<bool> ChangeUserWarning(string TelegramId, int Warning)
        {
            try
            {
                var score = await Scores.FindAsync(TelegramId);
                if (score != null)
                {
                    score.Warning += Warning;
                    await SaveChangesAsync();
                    await DisposeAsync();
                    return true;
                }
                else
                {
                    return false;
                }
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return false;
            }
        }
        public async Task<bool> CreateCode(string CodeId, string TimeStamp)
        {
            var code = new Code
            {
                CodeId = CodeId,
                TimeStamp = TimeStamp
            };
            try
            {
                Codes.Add(code);
                await SaveChangesAsync();
                await DisposeAsync();
                return true;
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return false;
            }
        }
        public async Task<bool> DeleteCode(string CodeId)
        {
            try
            {
                var code = await Codes.FindAsync(CodeId);
                if (code != null)
                {
                    Codes.Remove(code);
                    await SaveChangesAsync();
                    await DisposeAsync();
                    return true;
                }
                else
                {
                    return false;
                }
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return false;
            }
        }
        public async void DeleteLimitCode()
        {
            try
            {
                var codes = await Codes.Where(code => DateTime.Parse(code.TimeStamp) < DateTime.Now).ToListAsync();
                foreach (var code in codes)
                {
                        Codes.Remove(code);
                }
                await SaveChangesAsync();
                await DisposeAsync();
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
            }
        }

        public async Task<Dictionary<string, int>?> SettleUserScore(Dictionary<string, int> UserRatio, int TotalScore)
        {
            try
            {
                Dictionary<string, int> UserScore = new Dictionary<string, int>();
                foreach (var (UserId, Score) in UserRatio)
                {
                    var ScoreValue = (int)(Score * TotalScore * 0.5);
                    if (ScoreValue == 0)
                        ScoreValue = 1;
                    var score = await Scores.FindAsync(UserId);
                    if (score != null)
                        score.Value += ScoreValue;
                    else
                        await CreateScoreUser(UserId, ScoreValue);
                    UserScore[UserId] = ScoreValue;
                    await SaveChangesAsync();
                    await DisposeAsync();
                }
                return UserScore;
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return null;
            }
        }
        public int GetRenewValue()
        {
            try
            {
                int average = (int)Scores.Where(score => score.Value > 10).Average(score => score.Value);
                if (average <= 100)
                    average = 100;
                return average;
            }
            catch (Exception ex)
            {
                Logger.Error(ex.Message);
                return 100;
            }
        }
    }
}
