import * as React from 'react';
import { CssVarsProvider } from '@mui/joy/styles';
import {
  Typography,
  FormControl,
  FormLabel,
  Input,
  Button,
  Stack,
  Stepper,
  Step,
  StepIndicator,
  Textarea,
  Modal,
  ModalDialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Card,
  CardContent,
  CardActions,
  CardOverflow,
  Box,
  ModalClose,
} from '@mui/joy';
import {
  CheckRounded,
  DesignServicesOutlined,
  AddLinkOutlined,
  PhotoFilterOutlined,
  AutoAwesome,
  FaceRetouchingNatural,
} from '@mui/icons-material';
import { ServerResponse } from '../../typings/types';
import { Player } from '@lottiefiles/react-lottie-player';
import Animation from '../assets/Animation.json';

const App = () => {
  const [activeStep, setActiveStep] = React.useState(0);
  const [isStopping, setIsStopping] = React.useState(false);
  const [data, setData] = React.useState<ServerResponse | null>(null);
  const [url, setUrl] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [taskDesc, setTaskDesc] = React.useState('');
  const [personaDesc, setPersonaDesc] = React.useState('');
  const [personaModalOpen, setPersonaModalOpen] = React.useState(false);

  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState('');
  const [openModal, setOpenModal] = React.useState(false);

  const handleInit = () => {
    setIsLoading(true);
    setError('');
    parent.postMessage({ pluginMessage: { type: 'init', url, password } }, '*');
  };

  const handleExplore = (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    parent.postMessage({ pluginMessage: { type: 'explore', taskDesc, personaDesc } }, '*');
  };

  const handleStop = () => {
    setIsStopping(true);
    parent.postMessage({ pluginMessage: { type: 'stop-exploration' } }, '*');
  };

  const handleStatus = () => {
    parent.postMessage({ pluginMessage: { type: 'exploration-status' } }, '*');
  };

  const handleBack = () => {
    setOpenModal(true);
  };

  const handleConfirmBack = () => {
    handleStop();
    setOpenModal(false);
    setActiveStep(0);
    setUrl('');
    setPassword('');
    setTaskDesc('');
    setPersonaDesc('');
    setData(null);
    setError('');
  };

  const handleKeyDown = async (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
      handleExplore(e);
    }
  };

  React.useEffect(() => {
    window.onmessage = (event) => {
      const { type, data } = event.data.pluginMessage;
      setIsLoading(false);

      if (type === 'response') {
        if (data.status === 'success') {
          setData(data);
          if (!isStopping) {
            setActiveStep((prevStep) => prevStep + 1);
          }
        } else if (data.status === 'in_progress' || data.status === 'idle') {
          setData(data);
        } else {
          setError(data.message || 'An error occurred');
        }
      }

      setIsStopping(false);
    };
  }, [isStopping]);

  React.useEffect(() => {
    console.log('Active step changed:', activeStep);
  }, [activeStep]);

  return (
    <CssVarsProvider>
      <Box sx={{ maxWidth: 600, mx: 'auto', px: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Stepper orientation="vertical" key={activeStep}>
          <Step
            active={activeStep === 0}
            completed={activeStep > 0}
            indicator={
              <StepIndicator variant={activeStep === 0 ? 'solid' : 'soft'} color="primary">
                {activeStep > 0 ? <CheckRounded /> : <AddLinkOutlined />}
              </StepIndicator>
            }
          >
            <Typography level="title-md">Step 1</Typography>

            <Card variant="outlined">
              <CardOverflow
                variant="soft"
                color="primary"
                sx={{
                  justifyContent: 'center',
                  letterSpacing: '1px',
                  padding: '0.5rem 1rem',
                  borderColor: 'divider',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography sx={{ fontSize: 'xs', fontWeight: 'xl', textTransform: 'uppercase' }}>
                    Initialize
                  </Typography>
                  <Button color="neutral" variant="plain" onClick={handleBack} disabled={isLoading} size="sm">
                    Reset
                  </Button>
                </Box>
              </CardOverflow>
              {activeStep === 0 && (
                <>
                  <CardContent>
                    <FormControl error={!!error}>
                      <FormLabel>Figma Prototype URL</FormLabel>
                      <Input
                        value={url}
                        onChange={(e) => setUrl(e.target.value)}
                        placeholder="Enter the Figma Prototype URL"
                        disabled={isLoading}
                      />
                      {error ? <Typography color="danger">{error}</Typography> : null}
                    </FormControl>
                    <br />
                    <FormControl>
                      <FormLabel>Password (optional)</FormLabel>
                      <Input
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        placeholder="Enter the password if required"
                        disabled={isLoading}
                      />
                    </FormControl>
                  </CardContent>
                  <CardActions>
                    <Box sx={{ width: '100%', display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
                      <Button size="sm" onClick={handleInit} loading={isLoading} disabled={!url || isLoading}>
                        Initialize
                      </Button>
                    </Box>
                  </CardActions>
                </>
              )}
            </Card>
          </Step>
          <Step
            active={activeStep === 1}
            completed={activeStep > 1}
            indicator={
              <StepIndicator variant={activeStep === 1 ? 'solid' : 'soft'} color="primary">
                {activeStep > 1 ? <CheckRounded /> : <DesignServicesOutlined />}
              </StepIndicator>
            }
          >
            <Typography level="title-md">Step 2</Typography>

            <Card variant="outlined">
              <CardOverflow
                variant="soft"
                color="primary"
                sx={{
                  justifyContent: 'center',
                  letterSpacing: '1px',
                  padding: '0.5rem 1rem',
                  borderColor: 'divider',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography sx={{ fontSize: 'xs', fontWeight: 'xl', textTransform: 'uppercase' }}>
                    Task and Persona
                  </Typography>
                  <Button color="neutral" variant="plain" onClick={handleBack} disabled={isLoading} size="sm">
                    Reset
                  </Button>
                </Box>
              </CardOverflow>
              {activeStep === 1 && (
                <>
                  <CardContent>
                    <Textarea
                      placeholder="Please enter the description of the task you want to test"
                      disabled={isLoading}
                      value={taskDesc}
                      onChange={(e) => setTaskDesc(e.target.value)}
                      onKeyDown={handleKeyDown}
                      minRows={2}
                      maxRows={6}
                      size="md"
                      sx={{ minHeight: 240 }}
                      required
                      endDecorator={
                        <Box
                          sx={{
                            display: 'flex',
                            gap: 'var(--Textarea-paddingBlock)',
                            pt: 'var(--Textarea-paddingBlock)',
                            borderTop: '1px solid',
                            borderColor: 'divider',
                            flex: 'auto',
                          }}
                        >
                          <Button
                            variant="plain"
                            color="neutral"
                            onClick={() => setPersonaModalOpen(true)}
                            startDecorator={<FaceRetouchingNatural fontSize="small" />}
                          >
                            {/* if persona is empty, Button label is "Persona". If set use persona text and truncate the text */}
                            {personaDesc
                              ? personaDesc.length > 12
                                ? `${personaDesc.slice(0, 12)}...`
                                : personaDesc
                              : 'Persona'}
                          </Button>
                          <Button
                            color="primary"
                            variant="solid"
                            onClick={handleExplore}
                            disabled={!taskDesc || isLoading}
                            loading={isLoading}
                            loadingIndicator="Loading…"
                            startDecorator={<AutoAwesome fontSize="small" />}
                            size="sm"
                            sx={{ ml: 'auto' }}
                          >
                            Submit
                          </Button>
                        </Box>
                      }
                    />
                  </CardContent>
                </>
              )}
            </Card>
          </Step>
          <Step
            active={activeStep === 2}
            completed={activeStep > 2}
            indicator={
              <StepIndicator variant={activeStep === 2 ? 'solid' : 'soft'} color="primary">
                {activeStep > 2 ? <CheckRounded /> : <PhotoFilterOutlined />}
              </StepIndicator>
            }
          >
            <Typography level="title-md">Step 3</Typography>

            <Card variant="outlined" sx={{ backgroundColor: 'white' }}>
              <CardOverflow
                variant="soft"
                color="primary"
                sx={{
                  justifyContent: 'center',
                  letterSpacing: '1px',
                  padding: '0.5rem 1rem',
                  borderColor: 'divider',
                }}
              >
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Typography sx={{ fontSize: 'xs', fontWeight: 'xl', textTransform: 'uppercase' }}>
                    Generating Report
                  </Typography>
                  <Button color="neutral" variant="plain" onClick={handleBack} disabled={isLoading} size="sm">
                    Reset
                  </Button>
                </Box>
              </CardOverflow>

              {activeStep === 2 && (
                <>
                  <CardContent>
                    {error ? (
                      <Textarea
                        value={error}
                        readOnly
                        minRows={4}
                        maxRows={8}
                        size="md"
                        sx={{ minWidth: 480, minHeight: 240 }}
                      />
                    ) : data ? (
                      <>
                        <Player autoplay loop src={Animation} style={{ height: '160px', width: '160px' }} />
                        <Typography
                          component="pre"
                          level="body-sm"
                          color="neutral"
                          style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}
                        >
                          {data.message}
                        </Typography>
                      </>
                    ) : (
                      <>
                        <Player autoplay loop src={Animation} style={{ height: '160px', width: '160px' }} />
                        <Typography component="pre" level="body-sm">
                          &nbsp;
                        </Typography>
                      </>
                    )}
                    <br/>
                    <Button color="neutral" variant="outlined" onClick={handleStatus} sx={{ margin: 'auto', borderRadius: '16px' }}>
                      Check Status
                    </Button>
                  </CardContent>
                </>
              )}
            </Card>
          </Step>
        </Stepper>

        <Modal open={openModal} onClose={() => setOpenModal(false)}>
          <ModalDialog>
            <DialogTitle>Confirm Action</DialogTitle>
            <DialogContent>Stop the current exploration, and return to the initial step?</DialogContent>
            <DialogActions>
              <Button variant="solid" color="danger" onClick={handleConfirmBack}>
                Confirm
              </Button>
              <Button variant="plain" color="neutral" onClick={() => setOpenModal(false)}>
                Cancel
              </Button>
            </DialogActions>
          </ModalDialog>
        </Modal>
        <Modal open={personaModalOpen} onClose={() => setPersonaModalOpen(false)}>
          <ModalDialog layout="fullscreen">
            <ModalClose />
            <DialogTitle>Create Persona</DialogTitle>
            <DialogContent>
              <Stack spacing={2}>
                <Textarea
                  placeholder="(Optional) Please enter the description of the user persona you'd like me to emulate : "
                  autoFocus
                  value={personaDesc}
                  minRows={3}
                  maxRows={6}
                  onChange={(e) => setPersonaDesc(e.target.value)}
                />
              </Stack>
            </DialogContent>
            <DialogActions>
              <Button
                color="primary"
                variant="soft"
                onClick={() => {
                  setPersonaModalOpen(false);
                }}
              >
                Set Persona
              </Button>
              <Button
                variant="plain"
                color="neutral"
                onClick={() => {
                  setPersonaDesc('');
                  setPersonaModalOpen(false);
                }}
              >
                Reset
              </Button>
            </DialogActions>
          </ModalDialog>
        </Modal>
      </Box>
    </CssVarsProvider>
  );
};

export default App;
