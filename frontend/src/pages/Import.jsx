import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Label } from '../components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function Import() {
  const [file, setFile] = useState(null);
  const [memberId, setMemberId] = useState('');
  const [bankId, setBankId] = useState('');
  const [members, setMembers] = useState([]);
  const [banks, setBanks] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchMembersAndBanks();
  }, []);

  const fetchMembersAndBanks = async () => {
    try {
      const [membersRes, banksRes] = await Promise.all([
        axios.get(`${API}/family`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API}/banks`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setMembers(membersRes.data);
      setBanks(banksRes.data.filter((b) => b.active));
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Erro ao carregar membros e bancos');
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (selectedFile) => {
    const fileExtension = selectedFile.name.toLowerCase().split('.').pop();
    if (!['csv', 'ofx'].includes(fileExtension)) {
      toast.error('Apenas arquivos CSV ou OFX são aceitos');
      return;
    }
    setFile(selectedFile);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!file || !memberId || !bankId) {
      toast.error('Por favor, preencha todos os campos');
      return;
    }

    setUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('member_id', memberId);
      formData.append('bank_id', bankId);

      const response = await axios.post(`${API}/transactions/import`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success(
        <div className="flex items-center gap-2">
          <CheckCircle className="w-5 h-5" />
          <span>{response.data.message}</span>
        </div>
      );

      setFile(null);
      setMemberId('');
      setBankId('');
    } catch (error) {
      console.error('Upload error:', error);
      toast.error(
        error.response?.data?.detail ||
          'Erro ao importar transações'
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <div>
        <h1
          className="text-4xl md:text-5xl font-bold text-white mb-2"
          style={{ fontFamily: 'Manrope, sans-serif' }}
        >
          Importar Extratos
        </h1>
        <p className="text-slate-400 text-lg">
          Faça upload de arquivos CSV ou OFX para importar transações
        </p>
      </div>

      <Card className="glass-card border-slate-800">
        <CardHeader>
          <CardTitle className="text-xl font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Upload de Arquivo
          </CardTitle>
          <CardDescription className="text-slate-400">
            Arraste e solte ou clique para selecionar seu arquivo
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Drag and Drop Zone */}
            <div
              data-testid="file-upload-zone"
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`relative border-2 border-dashed rounded-xl p-12 text-center transition-all ${
                dragActive
                  ? 'border-blue-500 bg-blue-500/10'
                  : 'border-slate-700 hover:border-slate-600'
              }`}
            >
              <input
                type="file"
                data-testid="file-input"
                accept=".csv,.ofx"
                onChange={(e) => {
                  if (e.target.files && e.target.files[0]) {
                    handleFileChange(e.target.files[0]);
                  }
                }}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />

              <div className="space-y-4">
                {file ? (
                  <>
                    <FileText className="w-16 h-16 mx-auto text-green-400" />
                    <div>
                      <p className="text-lg font-semibold text-white">{file.name}</p>
                      <p className="text-sm text-slate-400">
                        {(file.size / 1024).toFixed(2)} KB
                      </p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      onClick={(e) => {
                        e.stopPropagation();
                        setFile(null);
                      }}
                      className="text-slate-400 hover:text-white"
                    >
                      Remover arquivo
                    </Button>
                  </>
                ) : (
                  <>
                    <Upload className="w-16 h-16 mx-auto text-slate-500" />
                    <div>
                      <p className="text-lg font-semibold text-white">
                        Arraste seu arquivo aqui
                      </p>
                      <p className="text-sm text-slate-400">
                        ou clique para selecionar (CSV, OFX)
                      </p>
                    </div>
                  </>
                )}
              </div>
            </div>

            {/* Member Selection */}
            <div className="space-y-2">
              <Label htmlFor="member" className="text-slate-300">
                Membro da Família
              </Label>
              <Select value={memberId} onValueChange={setMemberId}>
                <SelectTrigger
                  id="member"
                  data-testid="member-select"
                  className="bg-slate-950 border-slate-800 text-white h-12"
                >
                  <SelectValue placeholder="Selecione o membro" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800">
                  {members.length > 0 ? (
                    members.map((member) => (
                      <SelectItem
                        key={member.id}
                        value={member.id}
                        className="text-white hover:bg-slate-800"
                      >
                        {member.name}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="none" disabled className="text-slate-500">
                      Nenhum membro cadastrado
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
              {members.length === 0 && (
                <p className="text-sm text-amber-400 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Cadastre membros nas configurações primeiro
                </p>
              )}
            </div>

            {/* Bank Selection */}
            <div className="space-y-2">
              <Label htmlFor="bank" className="text-slate-300">
                Banco de Origem
              </Label>
              <Select value={bankId} onValueChange={setBankId}>
                <SelectTrigger
                  id="bank"
                  data-testid="bank-select"
                  className="bg-slate-950 border-slate-800 text-white h-12"
                >
                  <SelectValue placeholder="Selecione o banco" />
                </SelectTrigger>
                <SelectContent className="bg-slate-900 border-slate-800">
                  {banks.length > 0 ? (
                    banks.map((bank) => (
                      <SelectItem
                        key={bank.id}
                        value={bank.id}
                        className="text-white hover:bg-slate-800"
                      >
                        {bank.name}
                      </SelectItem>
                    ))
                  ) : (
                    <SelectItem value="none" disabled className="text-slate-500">
                      Nenhum banco cadastrado
                    </SelectItem>
                  )}
                </SelectContent>
              </Select>
              {banks.length === 0 && (
                <p className="text-sm text-amber-400 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  Cadastre bancos nas configurações primeiro
                </p>
              )}
            </div>

            {/* Submit Button */}
            <Button
              type="submit"
              data-testid="import-button"
              disabled={uploading || !file || !memberId || !bankId}
              className="w-full h-12 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-xl glow-blue button-glow"
            >
              {uploading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  Importando...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5 mr-2" />
                  Importar Transações
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="solid-card border-slate-800">
        <CardHeader>
          <CardTitle className="text-lg font-bold text-white" style={{ fontFamily: 'Manrope, sans-serif' }}>
            Formatos Aceitos
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-slate-400">
          <div>
            <p className="font-semibold text-white mb-1">CSV</p>
            <p className="text-sm">
              Arquivo deve conter colunas: date (data), description (descrição), amount (valor)
            </p>
          </div>
          <div>
            <p className="font-semibold text-white mb-1">OFX</p>
            <p className="text-sm">
              Formato padrão de extrato bancário (Open Financial Exchange)
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}