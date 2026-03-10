import { motion } from 'framer-motion';

export function GlassCard({ children, className = '', hover = true, ...props }) {
    return (
        <motion.div
            className={`glass-card p-6 ${hover ? '' : 'hover:transform-none hover:shadow-none hover:border-white/5'} ${className}`}
            whileHover={hover ? { y: -2 } : {}}
            transition={{ duration: 0.2 }}
            {...props}
        >
            {children}
        </motion.div>
    );
}

export function StatCard({ icon: Icon, label, value, color = 'primary', trend }) {
    const colorMap = {
        primary: 'from-primary-500/20 to-primary-600/10 text-primary-400',
        accent: 'from-accent-500/20 to-accent-600/10 text-accent-400',
        green: 'from-emerald-500/20 to-emerald-600/10 text-emerald-400',
        red: 'from-red-500/20 to-red-600/10 text-red-400',
        amber: 'from-amber-500/20 to-amber-600/10 text-amber-400',
    };

    return (
        <GlassCard>
            <div className="flex items-start justify-between">
                <div>
                    <p className="text-sm text-gray-400 mb-1">{label}</p>
                    <p className="text-3xl font-display font-bold text-white">{value}</p>
                    {trend && (
                        <p className={`text-xs mt-2 ${trend > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                            {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% vs last month
                        </p>
                    )}
                </div>
                <div className={`p-3 rounded-xl bg-gradient-to-br ${colorMap[color]}`}>
                    <Icon className="w-6 h-6" />
                </div>
            </div>
        </GlassCard>
    );
}

export function PageHeader({ title, subtitle, action }) {
    return (
        <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8"
        >
            <div>
                <h1 className="text-2xl lg:text-3xl font-display font-bold text-white">{title}</h1>
                {subtitle && <p className="text-gray-400 mt-1">{subtitle}</p>}
            </div>
            {action && <div>{action}</div>}
        </motion.div>
    );
}

export function Spinner({ size = 'md' }) {
    const sizeMap = { sm: 'w-5 h-5', md: 'w-8 h-8', lg: 'w-12 h-12' };
    return (
        <div className="flex items-center justify-center py-12">
            <div
                className={`${sizeMap[size]} border-2 border-primary-500/20 border-t-primary-500 rounded-full animate-spin`}
            />
        </div>
    );
}

export function Badge({ children, variant = 'default' }) {
    const variants = {
        default: 'bg-gray-500/10 text-gray-400 border-gray-500/20',
        success: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
        danger: 'bg-red-500/10 text-red-400 border-red-500/20',
        warning: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
        info: 'bg-primary-500/10 text-primary-400 border-primary-500/20',
    };

    return (
        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-lg text-xs font-medium border ${variants[variant]}`}>
            {children}
        </span>
    );
}

export function EmptyState({ icon: Icon, title, description, action }) {
    return (
        <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex flex-col items-center justify-center py-16 text-center"
        >
            {Icon && (
                <div className="p-4 rounded-2xl bg-primary-500/10 mb-4">
                    <Icon className="w-8 h-8 text-primary-400" />
                </div>
            )}
            <h3 className="text-lg font-semibold text-gray-300 mb-2">{title}</h3>
            <p className="text-gray-500 max-w-sm mb-6">{description}</p>
            {action}
        </motion.div>
    );
}
