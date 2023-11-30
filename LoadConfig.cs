using System;
using System.IO;
using System.Collections.Generic;
using YamlDotNet.Serialization;
using YamlDotNet.Serialization.NamingConventions;

namespace LoadConfig
{
    public class DataBase
    {
        public string? Host { get; set; }
        public required int Port { get; set; }
        public string? User { get; set; }
        public string? Password { get; set; }
        public string? Name { get; set; }
    }
    public class Telegram
    {
        public int API_ID { get; set; }
        public string? API_HASH { get; set; }
        public string? Token { get; set; }
        public string? Botname { get; set; }
        public string? RequiredChannel { get; set; }
        public string? ChatId { get; set; }
    }
    public class Emby
    {
        public string? Url { get; set; }
        public string? Token { get; set; }
    }
    public class Radarr
    {
        public string? Url { get; set; }
        public string? Token { get; set; }
    }
    public class Sonarr
    {
        public string? Url { get; set; }
        public string? Token { get; set; }
        public string? AnimeUrl { get; set; }
        public string? AnimeToken { get; set; }
    }
    public class Probe
    {
        public string? Url { get; set; }
        public string? Token { get; set; }
        public string? Id { get; set; }
    }
    public class Other
    {
        public required List<int> Admins { get; set; }
        public string? OMDB { get; set; }
        public string? Ratio { get; set; }
    }
    public class AppConfig
    {
        public required DataBase DataBase { get; set; }
        public required Telegram Telegram { get; set; }
        public required Emby Emby { get; set; }
        public required Radarr Radarr { get; set; }
        public required Sonarr Sonarr { get; set; }
        public required Probe Probe { get; set; }
        public required Other Other { get; set; }
    }

    class Configure
    {
        public static void InitConfig()
        {
            string filePath = "appconfig.yaml";
            var config = LoadConfigure();
            if (!File.Exists(filePath))
            {
                Console.WriteLine("配置文件不存在, 请按照提示填写配置文件");
                config.Other = GetUserInput<Other>("其他配置");
                config.DataBase = GetUserInput<DataBase>("数据库配置");
                config.Telegram = GetUserInput<Telegram>("Telegram配置");
                config.Emby = GetUserInput<Emby>("Emby配置");
                config.Radarr = GetUserInput<Radarr>("Radarr配置");
                config.Sonarr = GetUserInput<Sonarr>("Sonarr配置");
                config.Probe = GetUserInput<Probe>("Probe配置");

                SaveConfigure(config);
            }
        }

        public static AppConfig LoadConfigure()
        {
            string filePath = "appconfig.yaml";
            if (File.Exists(filePath))
            {
                var deserializer = new DeserializerBuilder()
                    .WithNamingConvention(CamelCaseNamingConvention.Instance)
                    .Build();

                using var reader = new StreamReader(filePath);
                return deserializer.Deserialize<AppConfig>(reader);
            }
            else
            {
                return new AppConfig
                {
                    Other = new Other() { Admins = new List<int>() },
                    DataBase = new DataBase() { Port = 3066 },
                    Telegram = new Telegram(),
                    Emby = new Emby(),
                    Radarr = new Radarr(),
                    Sonarr = new Sonarr(),
                    Probe = new Probe()
                };
            }
        }

        static void SaveConfigure(AppConfig config)
        {
            string filePath = "appconfig.yaml";
            var serializer = new SerializerBuilder()
                .WithNamingConvention(CamelCaseNamingConvention.Instance)
                .Build();

            using var writer = new StreamWriter(filePath);
            serializer.Serialize(writer, config);
        }

        static T GetUserInput<T>(string configName)
        {
            Console.WriteLine($"请输入 {configName} 的配置：");

            var properties = typeof(T).GetProperties();
            var instance = Activator.CreateInstance<T>();

            foreach (var property in properties)
            {
                Console.Write($"{property.Name}: ");
                string? input = Console.ReadLine();

                if (!string.IsNullOrEmpty(input))
                {
                    try
                    {
                        object value;
                        if (property.PropertyType == typeof(string))
                        {
                            value = input;
                        }
                        else if (property.PropertyType == typeof(List<int>))
                        {
                            value = input.Split(',')
                                .Select(s => int.TryParse(s, out int value) ? value : 0)
                                .ToList();
                        }
                        else
                        {
                            var converter = System.ComponentModel.TypeDescriptor.GetConverter(property.PropertyType);
                            value = converter.ConvertFromString(input);
                        }
                        if (value != null)
                        {
                            property.SetValue(instance, Convert.ChangeType(value, property.PropertyType));
                        }
                    }
                    catch (System.Exception)
                    {
                        Console.WriteLine($"无效的输入: {input}, 无法将 {input} 转换为 {property.PropertyType}");
                    }
                }
            }

            return instance;
        }
    }
}