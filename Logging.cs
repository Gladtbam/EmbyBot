using System;
using Microsoft.Extensions.Logging;

namespace Logging
{
    public class Logger
    {
        private readonly ILogger _logger;
        public Logger()
        {
            _logger = LoggerFactory.Create(builder =>
            {
                builder.AddFilter("Error", LogLevel.Error)
                       .AddFilter("Waring", LogLevel.Warning)
                       .AddFilter("Information", LogLevel.Information);
            }).CreateLogger<Logger>();
        }

        internal static void Error(string message)
        {
            throw new NotImplementedException();
        }
    }
}