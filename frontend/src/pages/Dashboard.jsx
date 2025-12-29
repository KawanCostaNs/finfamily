import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import {
  ArrowUpCircle,
  ArrowDownCircle,
  Wallet,
  TrendingUp,
  Calendar,
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
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
} from 'recharts';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const COLORS = ['#3b82f6', '#06b6d4', '#8b5cf6', '#10b981', '#f59e0b', '#f43f5e', '#ec4899', '#6366f1'];

export default function Dashboard() {
  const [month, setMonth] = useState(new Date().getMonth() + 1);
  const [year, setYear] = useState(new Date().getFullYear());
  const [summary, setSummary] = useState(null);
  const [categoryData, setCategoryData] = useState([]);
  const [monthlyData, setMonthlyData] = useState([]);
  const [loading, setLoading] = useState(true);

  const token = localStorage.getItem('token');

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      const [summaryRes, categoryRes, monthlyRes] = await Promise.all([
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
      ]);

      setSummary(summaryRes.data);
      setCategoryData(categoryRes.data);
      setMonthlyData(monthlyRes.data);
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
          <p className="text-slate-400 text-lg">Visão geral das suas finanças</p>
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
      )}

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Category Pie Chart */}
        <Card data-testid="category-chart" className="solid-card border-slate-800">
          <CardHeader>
            <CardTitle className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
              Despesas por Categoria
            </CardTitle>
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
                  <Legend
                    wrapperStyle={{ color: '#94a3b8' }}
                    iconType="circle"
                  />
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
      </div>
    </div>
  );
}