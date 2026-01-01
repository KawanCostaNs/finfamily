import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import {
  ArrowUpCircle,
  ArrowDownCircle,
  Wallet,
  TrendingUp,
  Calendar,
  TrendingDown,
  DollarSign,
  PieChart as PieChartIcon,
  Activity,
  Shield,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Legend,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line,
  AreaChart,
  Area,
} from 'recharts';
import GamificationSection from '../components/GamificationWidgets';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#3b82f6', '#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e', '#ec4899', '#6366f1'];

export default function Dashboard() {
  const navigate = useNavigate();
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [summary, setSummary] = useState(null);
  const [categoryData, setCategoryData] = useState([]);
  const [monthlyData, setMonthlyData] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [emergencyReserve, setEmergencyReserve] = useState(0);
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem('token');

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [summaryRes, categoryRes, monthlyRes, transactionsRes, reserveRes] = await Promise.all([
        axios.get(`${API}/dashboard/summary`, {
          params: { month, year },
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/dashboard/category-chart`, {
          params: { month, year },
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/dashboard/monthly-comparison`, {
          params: { year },
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/transactions`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/dashboard/emergency-reserve`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setSummary(summaryRes.data);
      setCategoryData(categoryRes.data);
      setMonthlyData(monthlyRes.data);
      setTransactions(transactionsRes.data);
      setEmergencyReserve(reserveRes.data.total);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Erro ao carregar dados do dashboard');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, [month, year]);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL',
    }).format(value);
  };

  const months = [
    { value: 1, label: 'Janeiro' },
    { value: 2, label: 'Fevereiro' },
    { value: 3, label: 'Março' },
    { value: 4, label: 'Abril' },
    { value: 5, label: 'Maio' },
    { value: 6, label: 'Junho' },
    { value: 7, label: 'Julho' },
    { value: 8, label: 'Agosto' },
    { value: 9, label: 'Setembro' },
    { value: 10, label: 'Outubro' },
    { value: 11, label: 'Novembro' },
    { value: 12, label: 'Dezembro' },
  ];

  const years = Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i);

  // Calculate balance trend
  const balanceTrend = monthlyData.map((m) => ({
    month: m.month,
    balance: m.income - m.expenses,
  }));

  // Calculate savings rate
  const savingsRate = summary
    ? summary.month_income > 0
      ? ((summary.month_income - summary.month_expenses) / summary.month_income) * 100
      : 0
    : 0;

  // Top expenses categories (top 5)
  const topExpenses = categoryData.slice(0, 5);

  // Recent transactions
  const recentTransactions = transactions
    .slice(0, 5)
    .map((t) => ({
      ...t,
      date: new Date(t.date),
    }))
    .sort((a, b) => b.date - a.date);

  // Calculate cumulative balance over months
  const cumulativeBalance = monthlyData.reduce((acc, curr, index) => {
    const prevBalance = index > 0 ? acc[index - 1].balance : 0;
    const currentBalance = prevBalance + curr.income - curr.expenses;
    acc.push({
      month: curr.month,
      balance: currentBalance,
    });
    return acc;
  }, []);

  if (loading && !summary) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400">Carregando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1
            className="text-4xl md:text-5xl font-bold text-white mb-2"
            style={{ fontFamily: 'Manrope, sans-serif' }}
          >
            Dashboard
          </h1>
          <p className="text-slate-400 text-lg">Visão geral completa das suas finanças</p>
        </div>

        <div className="flex gap-3">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-slate-400" />
            <Select value={month.toString()} onValueChange={(v) => setMonth(parseInt(v))}>
              <SelectTrigger data-testid="month-filter" className="w-[140px] bg-slate-900 border-slate-800 text-white">
                <SelectValue />
              </SelectTrigger>
              <SelectContent className="bg-slate-900 border-slate-800">
                {months.map((m) => (
                  <SelectItem key={m.value} value={m.value.toString()} className="text-white hover:bg-slate-800">
                    {m.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Select value={year.toString()} onValueChange={(v) => setYear(parseInt(v))}>
            <SelectTrigger data-testid="year-filter" className="w-[100px] bg-slate-900 border-slate-800 text-white">
              <SelectValue />
            </SelectTrigger>
            <SelectContent className="bg-slate-900 border-slate-800">
              {years.map((y) => (
                <SelectItem key={y} value={y.toString()} className="text-white hover:bg-slate-800">
                  {y}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card data-testid="previous-balance-card" className="glass-card border-slate-800 card-hover">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-slate-300 text-sm font-medium">
                  <Wallet className="w-4 h-4 text-slate-400" />
                  Saldo Anterior
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p
                  className="text-3xl font-bold text-white font-mono"
                  style={{ fontFamily: 'JetBrains Mono, monospace' }}
                >
                  {formatCurrency(summary.previous_balance)}
                </p>
              </CardContent>
            </Card>

            <Card data-testid="income-card" className="glass-card border-slate-800 card-hover">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-slate-300 text-sm font-medium">
                  <ArrowUpCircle className="w-4 h-4 text-green-400" />
                  Receita do Mês
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p
                  className="text-3xl font-bold text-green-400 font-mono glow-green"
                  style={{ fontFamily: 'JetBrains Mono, monospace' }}
                >
                  {formatCurrency(summary.month_income)}
                </p>
              </CardContent>
            </Card>

            <Card data-testid="expenses-card" className="glass-card border-slate-800 card-hover">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-slate-300 text-sm font-medium">
                  <ArrowDownCircle className="w-4 h-4 text-red-400" />
                  Despesas do Mês
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p
                  className="text-3xl font-bold text-red-400 font-mono glow-red"
                  style={{ fontFamily: 'JetBrains Mono, monospace' }}
                >
                  {formatCurrency(summary.month_expenses)}
                </p>
              </CardContent>
            </Card>

            <Card data-testid="final-balance-card" className="glass-card border-slate-800 card-hover">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-slate-300 text-sm font-medium">
                  <TrendingUp className="w-4 h-4 text-blue-400" />
                  Saldo Final
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p
                  className={`text-3xl font-bold font-mono ${
                    summary.final_balance >= 0 ? 'text-cyan-400 glow-cyan' : 'text-red-400 glow-red'
                  }`}
                  style={{ fontFamily: 'JetBrains Mono, monospace' }}
                >
                  {formatCurrency(summary.final_balance)}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Emergency Reserve Card - Destaque Especial */}
          <Card data-testid="emergency-reserve-card" className="glass-card border-amber-500/50 card-hover bg-gradient-to-br from-amber-900/20 to-amber-950/10">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-amber-300 text-lg font-medium">
                <Shield className="w-5 h-5 text-amber-400" />
                💰 Reserva de Emergência
              </CardTitle>
              <CardDescription className="text-amber-200/70">
                Total acumulado na reserva
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p
                className="text-4xl font-bold text-amber-400 font-mono glow-amber"
                style={{ fontFamily: 'JetBrains Mono, monospace' }}
              >
                {formatCurrency(emergencyReserve)}
              </p>
              <p className="text-sm text-amber-200/70 mt-2">
                {emergencyReserve >= (summary.month_expenses * 6) 
                  ? '✓ Excelente! Mais de 6 meses de despesas guardadas' 
                  : emergencyReserve >= (summary.month_expenses * 3)
                  ? '⚠ Bom! Procure atingir 6 meses de despesas'
                  : '⚡ Continue guardando para atingir 3-6 meses de despesas'}
              </p>
            </CardContent>
          </Card>
        </>
      )}

      {/* Additional Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="glass-card border-slate-800">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-slate-300 text-sm font-medium">
              <Activity className="w-4 h-4 text-purple-400" />
              Taxa de Poupança
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-purple-400 font-mono">
              {savingsRate.toFixed(1)}%
            </p>
            <p className="text-xs text-slate-500 mt-1">
              {savingsRate > 20 ? 'Excelente!' : savingsRate > 10 ? 'Bom' : 'Pode melhorar'}
            </p>
          </CardContent>
        </Card>

        <Card className="glass-card border-slate-800">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-slate-300 text-sm font-medium">
              <DollarSign className="w-4 h-4 text-cyan-400" />
              Total de Transações
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-cyan-400 font-mono">{transactions.length}</p>
            <button
              onClick={() => navigate('/transactions')}
              className="text-xs text-blue-400 hover:text-blue-300 mt-1"
            >
              Ver todas →
            </button>
          </CardContent>
        </Card>

        <Card className="glass-card border-slate-800">
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center gap-2 text-slate-300 text-sm font-medium">
              <PieChartIcon className="w-4 h-4 text-amber-400" />
              Categorias Ativas
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-amber-400 font-mono">{categoryData.length}</p>
            <p className="text-xs text-slate-500 mt-1">Com gastos este mês</p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Pie Chart */}
        <Card data-testid="category-chart" className="solid-card border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Despesas por Categoria
            </CardTitle>
            <CardDescription className="text-slate-400">Distribuição do mês selecionado</CardDescription>
          </CardHeader>
          <CardContent>
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ category, percentage }) => `${category}: ${percentage}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="amount"
                  >
                    {categoryData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc',
                    }}
                  />
                  <Legend wrapperStyle={{ color: '#94a3b8' }} iconType="circle" />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-slate-500">
                Nenhum dado de categoria disponível
              </div>
            )}
          </CardContent>
        </Card>

        {/* Monthly Bar Chart */}
        <Card data-testid="monthly-comparison-chart" className="solid-card border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Receita vs Despesa ({year})
            </CardTitle>
            <CardDescription className="text-slate-400">Comparativo mensal</CardDescription>
          </CardHeader>
          <CardContent>
            {monthlyData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={monthlyData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc',
                    }}
                  />
                  <Legend wrapperStyle={{ color: '#94a3b8' }} />
                  <Bar dataKey="income" fill="#10b981" name="Receita" radius={[8, 8, 0, 0]} />
                  <Bar dataKey="expenses" fill="#f43f5e" name="Despesa" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-slate-500">
                Nenhum dado mensal disponível
              </div>
            )}
          </CardContent>
        </Card>

        {/* Balance Trend Line Chart */}
        <Card className="solid-card border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Tendência de Saldo ({year})
            </CardTitle>
            <CardDescription className="text-slate-400">Resultado líquido mensal</CardDescription>
          </CardHeader>
          <CardContent>
            {balanceTrend.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={balanceTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc',
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="balance"
                    stroke="#06b6d4"
                    strokeWidth={3}
                    dot={{ fill: '#06b6d4', r: 6 }}
                    activeDot={{ r: 8 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-slate-500">
                Nenhum dado disponível
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cumulative Balance Area Chart */}
        <Card className="solid-card border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Evolução do Saldo Acumulado
            </CardTitle>
            <CardDescription className="text-slate-400">Crescimento patrimonial ao longo do ano</CardDescription>
          </CardHeader>
          <CardContent>
            {cumulativeBalance.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={cumulativeBalance}>
                  <defs>
                    <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                  <XAxis dataKey="month" stroke="#94a3b8" />
                  <YAxis stroke="#94a3b8" />
                  <Tooltip
                    formatter={(value) => formatCurrency(value)}
                    contentStyle={{
                      backgroundColor: '#1e293b',
                      border: '1px solid #334155',
                      borderRadius: '8px',
                      color: '#f8fafc',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="balance"
                    stroke="#8b5cf6"
                    strokeWidth={2}
                    fillOpacity={1}
                    fill="url(#colorBalance)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-[300px] text-slate-500">
                Nenhum dado disponível
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Gamification Section */}
      <GamificationSection />

      {/* Top Categories & Recent Transactions */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Top 5 Expenses */}
        <Card className="glass-card border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Top 5 Despesas
            </CardTitle>
            <CardDescription className="text-slate-400">Maiores gastos por categoria</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topExpenses.length > 0 ? (
                topExpenses.map((cat, index) => (
                  <div key={index} className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: COLORS[index % COLORS.length] }}
                      />
                      <span className="text-white font-medium">{cat.category}</span>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-mono font-semibold">{formatCurrency(cat.amount)}</p>
                      <p className="text-xs text-slate-400">{cat.percentage.toFixed(1)}%</p>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-center text-slate-500 py-8">Nenhuma despesa categorizada</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Recent Transactions */}
        <Card className="glass-card border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Transações Recentes
            </CardTitle>
            <CardDescription className="text-slate-400">Últimas movimentações</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {recentTransactions.length > 0 ? (
                recentTransactions.map((trans) => (
                  <div key={trans.id} className="flex items-center justify-between p-3 rounded-lg bg-slate-900/50">
                    <div>
                      <p className="text-white font-medium">{trans.description}</p>
                      <p className="text-xs text-slate-400">
                        {trans.date.toLocaleDateString('pt-BR')}
                      </p>
                    </div>
                    <p
                      className={`font-mono font-semibold ${
                        trans.type === 'receita' ? 'text-green-400' : 'text-red-400'
                      }`}
                    >
                      {trans.type === 'receita' ? '+' : '-'}
                      {formatCurrency(trans.amount)}
                    </p>
                  </div>
                ))
              ) : (
                <p className="text-center text-slate-500 py-8">Nenhuma transação encontrada</p>
              )}
            </div>
            {recentTransactions.length > 0 && (
              <Button
                onClick={() => navigate('/transactions')}
                variant="ghost"
                className="w-full mt-4 text-blue-400 hover:text-blue-300"
              >
                Ver todas as transações →
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
